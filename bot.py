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

# URL de Best Sellers (Usamos una URL más directa para evitar bloqueos)
AMAZON_URL = "https://www.amazon.com/zgbs/electronics/"

def enviar_telegram(mensaje):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except: pass

def rastrear_amazon_fisico():
    """Buscador con selectores de alta sensibilidad para Amazon 2026."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/',
        'DNT': '1'
    }
    
    try:
        response = requests.get(AMAZON_URL, headers=headers, timeout=20)
        if "captcha" in response.text.lower():
            return [], "Amazon pidió CAPTCHA (Bloqueo temporal)"
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # NUEVOS SELECTORES 2026: Buscamos por contenedor de producto
        items = soup.find_all('div', {'id': 'gridItemRoot'})
        if not items:
            items = soup.find_all('li', {'class': 'zg-item-immersion'})
        if not items:
            # Selector genérico de emergencia
            items = soup.select('div[data-asin]')

        productos_fisicos = []
        blacklist = ["plan", "subscription", "auto-renewal", "gift card", "digital", "membership", "blink", "cloud", "trial"]
        
        for item in items:
            if len(productos_fisicos) >= 10: break
            
            # Buscamos el nombre en cualquier etiqueta de texto dentro del item
            nombre_tag = item.find('h2') or item.find('div', class_='_cDE31_p13n-sc-css-line-clamp-3_2A69A') or item.find('span', class_='a-truncate-full')
            nombre = nombre_tag.get_text(strip=True) if nombre_tag else ""
            
            if not nombre or any(word in nombre.lower() for word in blacklist):
                continue

            link_tag = item.find('a', class_='a-link-normal')
            if link_tag:
                asin_path = link_tag.get('href').split('?')[0]
                link_final = f"https://www.amazon.com{asin_path}?tag={AMAZON_TAG}"
                
                productos_fisicos.append({
                    "producto": nombre,
                    "link": link_final
                })
        
        return productos_fisicos, None if productos_fisicos else "No se detectaron contenedores de productos físicos."
    except Exception as e:
        return [], str(e)

if __name__ == "__main__":
    print("🔎 CHM Brand: Escaneando con selectores actualizados...")
    lista, error = rastrear_amazon_fisico()
    
    if not lista:
        enviar_telegram(f"⚠️ *Atención CHM:* {error}")
    else:
        enviados = 0
        for p in lista:
            try:
                r = requests.post(MAKE_WEBHOOK_URL, json=p, timeout=15)
                if r.status_code == 200:
                    enviados += 1
                    time.sleep(12) 
            except: continue
        
        enviar_telegram(f"✅ *¡Éxito!* Encontrados {enviados} gadgets físicos reales.")
