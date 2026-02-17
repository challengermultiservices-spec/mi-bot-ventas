import requests
from bs4 import BeautifulSoup
import os
import time
import re

# ==========================================
# CONFIGURACIÓN ELITE CHM BRAND - USA TOTAL
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

    # Usamos ScraperAPI con ultra-renderizado y ubicación fija en USA
    target_url = "https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics/"
    proxy_url = "http://api.scraperapi.com"
    params = {
        'api_key': SCRAPER_API_KEY,
        'url': target_url,
        'render': 'true',
        'country_code': 'us',
        'wait_for_selector': 'div' # Esperamos a que la página cargue algo de contenido
    }

    try:
        print("🛡️ CHM Brand: Iniciando escaneo profundo de enlaces...")
        r = requests.get(proxy_url, params=params, timeout=90)
        soup = BeautifulSoup(r.content, 'html.parser')

        productos = []
        asins_vistos = set()
        blacklist = ["plan", "subscription", "gift card", "digital", "membership", "blink", "cloud", "trial", "auto-renewal"]

        # ESCANEO DE ENLACES (Nuclear Option)
        # Buscamos todos los enlaces que tengan el patrón /dp/ o /gp/product/
        enlaces = soup.find_all('a', href=re.compile(r'/(dp|gp/product)/[A-Z0-9]{10}'))

        for link in enlaces:
            if len(productos) >= 10: break
            
            href = link.get('href')
            asin_match = re.search(r'/(dp|gp/product)/([A-Z0-9]{10})', href)
            if not asin_match: continue
            
            # El ASIN es el grupo 2 en este patrón
            asin = asin_match.group(2)
            if asin in asins_vistos: continue

            # Buscamos el nombre: Prioridad 1: Texto del link. Prioridad 2: Alt de imagen interna.
            nombre = link.get_text(strip=True)
            if not nombre:
                img_tag = link.find('img')
                nombre = img_tag.get('alt', '') if img_tag else ""
            
            # Si sigue vacío, buscamos en el contenedor padre
            if not nombre:
                nombre = link.parent.get_text(strip=True)[:100]

            # Filtros de calidad y seguridad
            if len(nombre) < 12 or any(w in nombre.lower() for w in blacklist):
                continue

            asins_vistos.add(asin)
            productos.append({
                "producto": nombre[:120],
                "link": f"https://www.amazon.com/dp/{asin}?tag={AMAZON_TAG}"
            })

        if not productos:
            enviar_telegram("⚠️ Amazon bloqueó todos los identificadores. Probando nueva ruta mañana.")
            return

        # Enviamos los 10 productos finales a tu Excel de USA
        for p in productos:
            try:
                requests.post(MAKE_WEBHOOK_URL, json=p, timeout=15)
                time.sleep(12) # Pausa humana para asegurar las filas en Maryland
            except: continue

        enviar_telegram(f"✅ *¡Operación Exitosa!* Se inyectaron {len(productos)} productos reales detectados por ADN.")

    except Exception as e:
        enviar_telegram(f"❌ Error crítico: {str(e)}")

if __name__ == "__main__":
    main()
