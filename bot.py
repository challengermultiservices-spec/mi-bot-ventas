import requests
from bs4 import BeautifulSoup
import os
import time

# ==========================================
# CONFIGURACIÓN PROFESIONAL CHM BRAND
# ==========================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
AMAZON_TAG = "chmbrand-20"  # Tu código de afiliado
MAKE_WEBHOOK_URL = "https://hook.us2.make.com/iqydw7yi7jr9qwqpmad5vff1gejz2pbh"

# URL de Best Sellers de Electrónica (Alta rotación)
AMAZON_URL = "https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics/"

def enviar_telegram(mensaje):
    """Envía actualizaciones de estado a tu celular."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def rastrear_amazon_fisico():
    """Busca y filtra 10 productos físicos, ignorando basura digital."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/'
    }
    
    try:
        response = requests.get(AMAZON_URL, headers=headers, timeout=20)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Selectores universales para Amazon 2026
        items = soup.select('div#gridItemRoot')
        if not items:
            items = soup.select('li.zg-item-immersion')

        productos_fisicos = []
        # FILTRO DE SEGURIDAD: Evitamos lo que nos dio problemas hoy
        blacklist = ["plan", "subscription", "auto-renewal", "gift card", "digital", "membership", "blink", "cloud", "trial"]
        
        for item in items:
            if len(productos_fisicos) >= 10: break
            
            # Buscamos el nombre con múltiples opciones de selector
            nombre_tag = item.select_one('h2 span') or item.select_one('div._cDE31_p13n-sc-css-line-clamp-3_2A69A') or item.select_one('span.a-truncate-full')
            nombre = nombre_tag.get_text(strip=True) if nombre_tag else ""
            
            # Si es una suscripción o está vacío, lo saltamos
            if not nombre or any(word in nombre.lower() for word in blacklist):
                continue

            link_tag = item.find('a', class_='a-link-normal')
            if link_tag:
                # Limpiamos el link y añadimos tu tag de afiliado
                raw_link = "https://www.amazon.com" + link_tag.get('href').split('?')[0]
                productos_fisicos.append({
                    "producto": nombre,
                    "link": f"{raw_link}?tag={AMAZON_TAG}"
                })
        
        return productos_fisicos, None
    except Exception as e:
        return [], str(e)

if __name__ == "__main__":
    print("🔎 CHM Brand: Escaneando productos físicos reales...")
    lista, error = rastrear_amazon_fisico()
    
    if not lista:
        enviar_telegram(f"⚠️ *Alerta:* No se encontraron productos físicos hoy. Error: {error}")
    else:
        enviados = 0
        for p in lista:
            # Enviamos cada producto individualmente para crear 10 filas
            try:
                r = requests.post(MAKE_WEBHOOK_URL, json=p, timeout=15)
                if r.status_code == 200:
                    enviados += 1
                    # Pausa de 12 segundos para que Google Sheets no se sature
                    time.sleep(12) 
            except Exception as ex:
                print(f"Error enviando producto: {ex}")
        
        enviar_telegram(f"✅ *¡Éxito!* Se procesaron {enviados} productos físicos para CHM Brand.")
