import requests
from bs4 import BeautifulSoup
import os
import time

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
AMAZON_TAG = "chmbrand-20"
MAKE_WEBHOOK_URL = "https://hook.us2.make.com/iqydw7yi7jr9qwqpmad5vff1gejz2pbh"
AMAZON_URL = "https://www.amazon.com/gp/bestsellers/electronics/"

# ==========================================
# 2. FUNCIONES
# ==========================================

def enviar_telegram(mensaje):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except: pass

def rastrear_amazon_top_10():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }

    try:
        response = requests.get(AMAZON_URL, headers=headers, timeout=20)
        if response.status_code != 200: return [], f"Error Amazon: {response.status_code}"

        soup = BeautifulSoup(response.content, 'lxml')
        items = soup.select('#gridItemRoot')
        
        productos_encontrados = []
        
        for item in items:
            if len(productos_encontrados) >= 10: break

            img = item.select_one('img')
            link = item.select_one('a.a-link-normal')
            
            nombre = img.get('alt', "") if img else ""
            
            # FILTRO: Solo productos físicos reales
            if any(x in nombre.lower() for x in ["subscription", "plan", "membership", "digital", "blink"]):
                continue

            imagen_url = img.get('src') if img else None
            if imagen_url and "._AC" in imagen_url:
                imagen_url = imagen_url.split("._AC")[0] + "._AC_SL1000_.jpg"

            link_final = "https://www.amazon.com"
            if link:
                href = link.get('href')
                base = href if href.startswith('http') else "https://www.amazon.com" + href
                link_final = f"{base.split('?')[0]}?tag={AMAZON_TAG}"

            if nombre and imagen_url:
                productos_encontrados.append({
                    "producto": nombre,
                    "imagen": imagen_url,
                    "link": link_final
                })

        return productos_encontrados, None
    except Exception as e:
        return [], str(e)

# ==========================================
# 3. EJECUCIÓN PRINCIPAL
# ==========================================

if __name__ == "__main__":
    print("🚀 Iniciando Escaneo para CHM Brand...")
    lista_productos, error = rastrear_amazon_top_10()

    if not lista_productos:
        enviar_telegram(f"❌ No se encontraron productos reales. Error: {error}")
        exit(1)

    enviados = 0
    for p in lista_productos:
        try:
            r = requests.post(MAKE_WEBHOOK_URL, json=p)
            if r.status_code == 200:
                enviados += 1
                print(f"✅ Enviado: {p['producto']}")
                time.sleep(2)
        except:
            print(f"❌ Error enviando {p['producto']}")

    enviar_telegram(f"✅ *¡Éxito!* Se enviaron {enviados} productos reales a Make.")
