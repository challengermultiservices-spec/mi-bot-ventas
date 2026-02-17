import requests
from bs4 import BeautifulSoup
import os
import time
import random

# ==========================================
# CONFIGURACIÓN PROFESIONAL CHM BRAND
# ==========================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
AMAZON_TAG = "chmbrand-20" #
MAKE_WEBHOOK_URL = "https://hook.us2.make.com/iqydw7yi7jr9qwqpmad5vff1gejz2pbh"

# URL directa a Electrónica para evitar redirecciones
AMAZON_URL = "https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics/ref=zg_bs_nav_electronics_0"

def enviar_telegram(mensaje):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except: pass

def rastrear_amazon_fisico():
    """Bot con identidad rotativa para evitar bloqueos de Amazon."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': 'https://www.google.com/',
        'Device-Memory': '8'
    }
    
    try:
        session = requests.Session()
        response = session.get(AMAZON_URL, headers=headers, timeout=25)
        
        if response.status_code != 200:
            return [], f"Error de conexión: {response.status_code}"
            
        if "api-services-support@amazon.com" in response.text:
            return [], "Amazon detectó el bot (Robot Check). Reintentando..."

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # TRIPLE SELECTOR: Si uno falla, el otro busca
        items = soup.select('div#gridItemRoot') # Estándar
        if not items:
            items = soup.select('div.p13n-grid-col') # Alternativo 1
        if not items:
            items = soup.select('li.zg-item-immersion') # Alternativo 2

        productos_fisicos = []
        blacklist = ["plan", "subscription", "auto-renewal", "gift card", "digital", "membership", "blink", "cloud", "trial"]
        
        for item in items:
            if len(productos_fisicos) >= 10: break
            
            # Buscamos el nombre en cualquier rincón del contenedor
            nombre_tag = item.find('h2') or item.select_one('div._cDE31_p13n-sc-css-line-clamp-3_2A69A') or item.select_one('span.a-truncate-full')
            nombre = nombre_tag.get_text(strip=True) if nombre_tag else ""
            
            # FILTRO: Solo productos reales
            if not nombre or any(word in nombre.lower() for word in blacklist):
                continue

            link_tag = item.find('a', class_='a-link-normal')
            if link_tag:
                asin_path = link_tag.get('href').split('?')[0]
                # Limpieza absoluta del link para asegurar comisión
                link_final = f"https://www.amazon.com{asin_path}?tag={AMAZON_TAG}"
                
                productos_fisicos.append({
                    "producto": nombre,
                    "link": link_final
                })
        
        if not productos_fisicos:
            return [], "No se encontraron productos físicos en la estructura actual."
            
        return productos_fisicos, None
    except Exception as e:
        return [], str(e)

if __name__ == "__main__":
    print("🔎 CHM Brand: Iniciando rastreo profundo...")
    lista, error = rastrear_amazon_fisico()
    
    if not lista:
        enviar_telegram(f"⚠️ *Atención Jorge:* {error}")
    else:
        enviados = 0
        for p in lista:
            try:
                # Cada producto se envía con una identidad única a Make
                r = requests.post(MAKE_WEBHOOK_URL, json=p, timeout=15)
                if r.status_code == 200:
                    enviados += 1
                    time.sleep(random.randint(8, 12)) # Pausa humana para evitar bloqueos
            except: continue
        
        enviar_telegram(f"✅ *¡Éxito!* Encontrados {enviados} gadgets para CHM Brand.")
