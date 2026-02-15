import requests
from bs4 import BeautifulSoup
import os
import time

# ==========================================
# CONFIGURACIÓN PROFESIONAL CHM BRAND
# ==========================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
AMAZON_TAG = "chmbrand-20"
MAKE_WEBHOOK_URL = "https://hook.us2.make.com/iqydw7yi7jr9qwqpmad5vff1gejz2pbh"
# Categoría de Gadgets de Electrónica (Alta rotación para TikTok)
AMAZON_URL = "https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics/"

def enviar_telegram(mensaje):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except: pass

def rastrear_amazon_top_10():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/'
    }
    try:
        response = requests.get(AMAZON_URL, headers=headers, timeout=20)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Selectores universales actualizados para 2026
        items = soup.select('div#gridItemRoot')
        if not items:
            items = soup.select('li.zg-item-immersion') # Selector alternativo

        productos_encontrados = []
        for item in items:
            if len(productos_encontrados) >= 10: break
            
            # Buscamos el nombre con múltiples opciones de etiquetas
            nombre_tag = item.select_one('div._cDE31_p13n-sc-css-line-clamp-3_2A69A')
            if not nombre_tag: nombre_tag = item.select_one('span.a-truncate-full')
            
            nombre = nombre_tag.get_text(strip=True) if nombre_tag else "Producto sin nombre"
            
            # Filtro reforzado contra contenido digital y suscripciones
            if any(x in nombre.lower() for x in ["subscription", "gift card", "digital", "membership", "blink"]):
                continue

            link_tag = item.find('a', class_='a-link-normal')
            img_tag = item.find('img')

            if link_tag and img_tag:
                link_raw = "https://www.amazon.com" + link_tag.get('href').split('?')[0]
                productos_encontrados.append({
                    "producto": nombre,
                    "imagen": img_tag.get('src'),
                    "link": f"{link_raw}?tag={AMAZON_TAG}"
                })
        return productos_encontrados, None
    except Exception as e:
        return [], str(e)

if __name__ == "__main__":
    print("🔎 Escaneando Amazon para CHM Brand...")
    lista, error = rastrear_amazon_top_10()
    
    if not lista:
        enviar_telegram(f"⚠️ Alerta: Amazon aplicó un cambio drástico. No se detectaron productos. Error: {error}")
    else:
        enviados = 0
        for p in lista:
            # Enviamos a Make aprovechando tu nuevo plan de pago
            try:
                r = requests.post(MAKE_WEBHOOK_URL, json=p, timeout=10)
                if r.status_code == 200:
                    enviados += 1
                    time.sleep(10) # Pausa para procesar en Make sin saturar
            except: pass
        
        enviar_telegram(f"✅ *¡Éxito Total!* Se enviaron {enviados} productos reales a tu inventario de Make.")
