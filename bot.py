import requests
from bs4 import BeautifulSoup
import os
import time
import re

# ==========================================
# CONFIGURACIÓN CHM BRAND - USA TOTAL
# ==========================================
SCRAPER_API_KEY = os.getenv('SCRAPERAPI_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
AMAZON_TAG = "chmbrand-20"
MAKE_WEBHOOK_URL = "https://hook.us2.make.com/iqydw7yi7jr9qwqpmad5vff1gejz2pbh"

def enviar_telegram(mensaje):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def main():
    if not SCRAPER_API_KEY:
        enviar_telegram("❌ Error: Llave SCRAPERAPI_KEY no encontrada.")
        return

    # Escudo ScraperAPI con instrucciones de ESPERA (render=true)
    target_url = "https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics/"
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}&render=true&country_code=us"

    try:
        print("🔎 Simulando navegación humana en USA...")
        r = requests.get(proxy_url, timeout=90)
        
        if r.status_code != 200:
            enviar_telegram(f"❌ Error de acceso: {r.status_code}")
            return

        soup = BeautifulSoup(r.content, 'html.parser')
        
        # BUSCADOR DE ADN (Enlaces de producto)
        # Buscamos patrones /dp/ o /gp/product/ que son universales en Amazon
        enlaces = soup.find_all('a', href=re.compile(r'/(dp|gp/product)/[A-Z0-9]{10}'))
        
        productos = []
        asins_vistos = set()
        blacklist = ["plan", "subscription", "gift card", "digital", "membership", "blink", "cloud", "trial"]

        for link in enlaces:
            if len(productos) >= 10: break
            
            href = link.get('href')
            match = re.search(r'/(dp|gp/product)/([A-Z0-9]{10})', href)
            if not match: continue
            
            asin = match.group(2)
            if asin in asins_vistos: continue

            # Extraemos el nombre: Texto del link o Alt de la imagen
            nombre = link.get_text(strip=True)
            if not nombre:
                img = link.find('img')
                nombre = img.get('alt', '') if img else ""
            
            # Si el nombre es muy corto o es basura digital, saltamos
            if len(nombre) < 15 or any(w in nombre.lower() for w in blacklist):
                continue

            asins_vistos.add(asin)
            productos.append({
                "producto": nombre[:120],
                "link": f"https://www.amazon.com/dp/{asin}?tag={AMAZON_TAG}"
            })

        if not productos:
            enviar_telegram("⚠️ Amazon ocultó los datos en esta simulación. Reintentando...")
            return

        # Enviamos los 10 ganadores a tu Excel
        for p in productos:
            try:
                requests.post(MAKE_WEBHOOK_URL, json=p, timeout=20)
                # Pausa para que Make y Google Sheets procesen sin errores
                time.sleep(15) 
            except: continue

        enviar_telegram(f"✅ *CHM Brand USA:* ¡Misión cumplida! Se inyectaron {len(productos)} productos únicos.")

    except Exception as e:
        enviar_telegram(f"❌ Error crítico: {str(e)}")

if __name__ == "__main__":
    main()
