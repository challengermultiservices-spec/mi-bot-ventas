import requests
from bs4 import BeautifulSoup
import os
import time
import re

# ==========================================
# CONFIGURACIÓN ELITE CHM BRAND
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
    # Verificación de la llave inyectada por el YAML
    if not SCRAPER_API_KEY:
        enviar_telegram("❌ Error: No se detectó la llave en el entorno de GitHub.")
        return

    # Usamos tu escudo ScraperAPI para todo USA
    target_url = "https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics/"
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}&render=true&country_code=us"

    try:
        print("🛡️ CHM Brand: Iniciando túnel seguro...")
        r = requests.get(proxy_url, timeout=60)
        
        if r.status_code != 200:
            enviar_telegram(f"❌ Error de ScraperAPI: {r.status_code}. Revisa tu cuenta.")
            return

        soup = BeautifulSoup(r.content, 'html.parser')
        # Buscamos los productos con el diseño más reciente de Amazon
        items = soup.select('div#gridItemRoot') or soup.select('li.zg-item-immersion')

        productos = []
        asins_vistos = set() # Evita repetidos (Solución a image_3ee9e3.png)
        blacklist = ["plan", "subscription", "gift card", "digital", "membership", "blink", "cloud", "trial"]

        for item in items:
            if len(productos) >= 10: break
            
            name_tag = item.find('h2') or item.select_one('div._cDE31_p13n-sc-css-line-clamp-3_2A69A')
            link_tag = item.find('a', class_='a-link-normal')

            if name_tag and link_tag:
                nombre = name_tag.get_text(strip=True)
                # Extraemos el código ASIN único del enlace
                asin_match = re.search(r'\/dp\/([A-Z0-9]{10})', link_tag.get('href'))
                asin = asin_match.group(1) if asin_match else None

                # Filtro: No repetidos y no basura digital
                if not asin or asin in asins_vistos: continue
                if any(w in nombre.lower() for w in blacklist): continue

                asins_vistos.add(asin)
                productos.append({
                    "producto": nombre[:120],
                    "link": f"https://www.amazon.com/dp/{asin}?tag={AMAZON_TAG}"
                })

        # Enviamos los 10 productos finales al Webhook de Make
        for p in productos:
            requests.post(MAKE_WEBHOOK_URL, json=p)
            time.sleep(12) # Pausa para que Google Sheets cree las filas una a una

        enviar_telegram(f"✅ *¡Operación Exitosa!* Se inyectaron {len(productos)} productos únicos de USA.")

    except Exception as e:
        enviar_telegram(f"❌ Error crítico en el bot: {str(e)}")

if __name__ == "__main__":
    main()
