import requests
from bs4 import BeautifulSoup
import os
import time
import random
import re

# ==========================================
# CONFIGURACIÓN PROFESIONAL CHM BRAND
# ==========================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
AMAZON_TAG = "chmbrand-20"
MAKE_WEBHOOK_URL = "https://hook.us2.make.com/iqydw7yi7jr9qwqpmad5vff1gejz2pbh"
AMAZON_URL = "https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics/"

def enviar_telegram(mensaje):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except: pass

def rastrear_amazon_universal():
    """Buscador que rastrea cualquier link de producto sin depender de clases CSS."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/'
    }
    
    try:
        response = requests.get(AMAZON_URL, headers=headers, timeout=30)
        # Si Amazon nos bloquea con un Captcha, lo detectamos
        if "captcha" in response.text.lower():
            return [], "Amazon detectó el bot y pidió Captcha. Reintentar en una hora."
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # BUSCADOR POR ADN: Buscamos links que contengan /dp/ (patrón de producto)
        links = soup.find_all('a', href=re.compile(r'\/dp\/[A-Z0-9]{10}'))
        
        productos_fisicos = []
        asins_vistos = set()
        blacklist = ["plan", "subscription", "auto-renewal", "gift card", "digital", "membership", "blink", "cloud", "trial"]
        
        for link in links:
            if len(productos_fisicos) >= 10: break
            
            href = link.get('href')
            # Extraer el código ASIN del producto
            match = re.search(r'\/dp\/([A-Z0-9]{10})', href)
            if not match: continue
            asin = match.group(1)
            
            if asin in asins_vistos: continue
            
            # Buscamos el nombre: puede estar en el texto del link o en una imagen dentro
            nombre = link.get_text(strip=True)
            if not nombre:
                img = link.find('img')
                nombre = img.get('alt', '') if img else ""
            
            # Filtro: debe tener un nombre decente y no ser basura digital
            if len(nombre) < 15 or any(word in nombre.lower() for word in blacklist):
                continue

            asins_vistos.add(asin)
            link_final = f"https://www.amazon.com/dp/{asin}?tag={AMAZON_TAG}"
            productos_fisicos.append({"producto": nombre, "link": link_final})
            
        return productos_fisicos, None
    except Exception as e:
        return [], str(e)

if __name__ == "__main__":
    print("🔎 Iniciando rastreo universal para CHM Brand...")
    lista, error = rastrear_amazon_universal()
    
    if not lista:
        enviar_telegram(f"⚠️ *Atención Jorge:* {error or 'Amazon ocultó la lista de productos hoy.'}")
    else:
        enviados = 0
        for p in lista:
            try:
                # Envío individual para asegurar las 10 filas
                r = requests.post(MAKE_WEBHOOK_URL, json=p, timeout=20)
                if r.status_code == 200:
                    enviados += 1
                    time.sleep(random.randint(12, 18)) 
            except: continue
        
        enviar_telegram(f"✅ *Éxito:* Se enviaron {enviados} productos reales a tu Excel.")
