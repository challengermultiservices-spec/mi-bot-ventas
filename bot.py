import requests
from bs4 import BeautifulSoup
import os
import time
import random
import re

# ==========================================
# CONFIGURACIÓN ELITE CHM BRAND - USA TOTAL
# ==========================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
AMAZON_TAG = "chmbrand-20" 
MAKE_WEBHOOK_URL = "https://hook.us2.make.com/iqydw7yi7jr9qwqpmad5vff1gejz2pbh"

# URL de Best Sellers Electrónica USA
AMAZON_URL = "https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics/"

def enviar_telegram(mensaje):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except: pass

def rastrear_top_10_usa():
    """Extrae 10 productos únicos evitando duplicados y basura digital."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/'
    }
    
    try:
        session = requests.Session()
        response = session.get(AMAZON_URL, headers=headers, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Selectores universales
        items = soup.select('div#gridItemRoot') or soup.select('li.zg-item-immersion')
        
        productos_finales = []
        asins_vistos = set() # Evita repetidos (Solución a image_3ee9e3.png)
        blacklist = ["plan", "subscription", "auto-renewal", "gift card", "digital", "membership", "blink", "cloud", "trial"]
        
        for item in items:
            if len(productos_finales) >= 10: break
            
            nombre_tag = item.find('h2') or item.select_one('div._cDE31_p13n-sc-css-line-clamp-3_2A69A')
            link_tag = item.find('a', class_='a-link-normal')
            
            if nombre_tag and link_tag:
                nombre = nombre_tag.get_text(strip=True)
                asin_match = re.search(r'\/dp\/([A-Z0-9]{10})', link_tag.get('href'))
                asin = asin_match.group(1) if asin_match else None

                # FILTROS DE SEGURIDAD
                if not asin or asin in asins_vistos: continue
                if any(word in nombre.lower() for word in blacklist): continue

                link_final = f"https://www.amazon.com/dp/{asin}?tag={AMAZON_TAG}"
                asins_vistos.add(asin)
                productos_finales.append({"producto": nombre[:120], "link": link_final})
        
        return productos_finales
    except: return []

if __name__ == "__main__":
    print("🔎 CHM Brand: Iniciando barrido nacional...")
    lista = rastrear_top_10_usa()
    
    if not lista:
        enviar_telegram("⚠️ Amazon bloqueó la vista o no se encontraron productos físicos hoy.")
    else:
        enviados = 0
        for p in lista:
            try:
                # Envío individual para forzar 10 filas separadas
                r = requests.post(MAKE_WEBHOOK_URL, json=p, timeout=20)
                if r.status_code == 200:
                    enviados += 1
                    # PAUSA CRÍTICA: 25 segundos para asegurar que Google Sheets escriba bien
                    time.sleep(random.randint(20, 30)) 
            except: continue
        
        enviar_telegram(f"✅ *¡Éxito!* Se inyectaron {enviados} productos únicos en tu Excel.")
