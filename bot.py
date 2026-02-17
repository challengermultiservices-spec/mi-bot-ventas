import requests
from bs4 import BeautifulSoup
import os
import time
import re

# ==========================================
# CONFIGURACIÓN MAESTRA - CHM BRAND USA
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
        enviar_telegram("❌ Error: No se detectó la llave SCRAPERAPI_KEY en GitHub.")
        return

    # Usamos ScraperAPI con ultra-renderizado para ver la página como un humano real
    target_url = "https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics/"
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}&render=true&country_code=us"

    try:
        print("🛡️ CHM Brand: Iniciando escaneo profundo...")
        r = requests.get(proxy_url, timeout=90)
        soup = BeautifulSoup(r.content, 'html.parser')

        productos = []
        asins_vistos = set()
        blacklist = ["plan", "subscription", "gift card", "digital", "membership", "blink", "cloud", "trial", "auto-renewal"]

        # BUSCADOR POR ADN: Rastreamos cada link de la página buscando el patrón de Amazon
        enlaces = soup.find_all('a', href=re.compile(r'/(dp|gp/product)/[A-Z0-9]{10}'))

        for link in enlaces:
            if len(productos) >= 10: break
            
            href = link.get('href')
            match = re.search(r'/(dp|gp/product)/([A-Z0-9]{10})', href)
            if not match: continue
            
            asin = match.group(2)
            if asin in asins_vistos: continue

            # Intentamos sacar el nombre de 3 formas distintas
            nombre = link.get_text(strip=True)
            if not nombre:
                img = link.find('img')
                nombre = img.get('alt', '') if img else ""
            if not nombre:
                # Si falla lo anterior, buscamos en el contenedor de al lado
                nombre = link.parent.get_text(strip=True)[:100]

            # Filtro de calidad
            if len(nombre) < 15 or any(w in nombre.lower() for w in blacklist):
                continue

            asins_vistos.add(asin)
            productos.append({
                "producto": nombre[:120],
                "link": f"https://www.amazon.com/dp/{asin}?tag={AMAZON_TAG}"
            })

        if not productos:
            enviar_telegram("⚠️ Amazon bloqueó el escaneo de nombres hoy. Reintentando mañana.")
            return

        # Inyectamos los 10 productos en tu Google Sheet (vía Make)
        for p in productos:
            try:
                requests.post(MAKE_WEBHOOK_URL, json=p, timeout=15)
                time.sleep(12) # Pausa vital para evitar bloqueos en el Excel
            except: continue

        enviar_telegram(f"✅ *¡Operación Exitosa!* Se inyectaron {len(productos)} productos reales detectados por ADN.")

    except Exception as e:
        enviar_telegram(f"❌ Error crítico: {str(e)}")

if __name__ == "__main__":
    main()
