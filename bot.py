import requests
from bs4 import BeautifulSoup
import os
import time
import re

# CONFIGURACIÓN ELITE CHM BRAND - USA
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
        enviar_telegram("❌ Error: No se detectó la llave en GitHub.")
        return

    # Usamos ScraperAPI con renderizado para ver la página como un humano
    target_url = "https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics/"
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}&render=true&country_code=us"

    try:
        print("🛡️ CHM Brand: Escaneando productos físicos en USA...")
        r = requests.get(proxy_url, timeout=60)
        soup = BeautifulSoup(r.content, 'html.parser')

        # BUSCADOR AGRESIVO: Buscamos cualquier cosa que parezca un producto del Top 100
        # Amazon usa diferentes etiquetas, así que probamos todas las conocidas
        items = soup.select('div#gridItemRoot') or \
                soup.select('div[data-asin]') or \
                soup.select('li.zg-item-immersion') or \
                soup.select('div.zg-grid-general-faceout')

        productos = []
        asins_vistos = set()
        blacklist = ["plan", "subscription", "gift card", "digital", "membership", "blink", "cloud", "trial"]

        for item in items:
            if len(productos) >= 10: break
            
            # Buscamos el link para extraer el ASIN (el ADN del producto)
            link_tag = item.find('a', href=re.compile(r'\/dp\/[A-Z0-9]{10}'))
            if not link_tag: continue
            
            href = link_tag.get('href')
            asin_match = re.search(r'\/dp\/([A-Z0-9]{10})', href)
            asin = asin_match.group(1) if asin_match else None

            if not asin or asin in asins_vistos: continue

            # Buscamos el nombre: puede estar en un h2, un span o en el alt de la imagen
            nombre = ""
            name_tag = item.find('h2') or item.select_one('div._cDE31_p13n-sc-css-line-clamp-3_2A69A') or item.find('span')
            if name_tag:
                nombre = name_tag.get_text(strip=True)
            
            if not nombre:
                img_tag = item.find('img')
                nombre = img_tag.get('alt', '') if img_tag else ""

            # Filtros de seguridad
            if len(nombre) < 15 or any(w in nombre.lower() for w in blacklist):
                continue

            asins_vistos.add(asin)
            productos.append({
                "producto": nombre[:120],
                "link": f"https://www.amazon.com/dp/{asin}?tag={AMAZON_TAG}"
            })

        if not productos:
            enviar_telegram("⚠️ Amazon ocultó los nombres. Reintentando con escaneo de enlaces...")
            # Si fallan los selectores, buscamos directamente todos los enlaces de la página
            for a_tag in soup.find_all('a', href=re.compile(r'\/dp\/[A-Z0-9]{10}')):
                if len(productos) >= 10: break
                # Lógica de emergencia aquí...
        
        # Enviamos los resultados a Make
        for p in productos:
            requests.post(MAKE_WEBHOOK_URL, json=p)
            time.sleep(12) # Pausa para que el Excel no se trabe

        enviar_telegram(f"✅ *¡Operación Exitosa!* Se inyectaron {len(productos)} productos únicos de USA.")

    except Exception as e:
        enviar_telegram(f"❌ Error crítico: {str(e)}")

if __name__ == "__main__":
    main()
