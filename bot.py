import requests
from bs4 import BeautifulSoup
import os
import re

# CONFIGURACIÓN CHM BRAND
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
    target_url = "https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics/"
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}&render=true&country_code=us"

    try:
        r = requests.get(proxy_url, timeout=120)
        soup = BeautifulSoup(r.content, 'html.parser')
        enlaces = soup.find_all('a', href=re.compile(r'/(dp|gp/product)/[A-Z0-9]{10}'))
        
        lista_para_make = []
        asins_vistos = set()

        for link in enlaces:
            if len(lista_para_make) >= 10: break
            asin_match = re.search(r'/(dp|gp/product)/([A-Z0-9]{10})', link.get('href'))
            if not asin_match: continue
            asin = asin_match.group(2)
            
            if asin not in asins_vistos:
                nombre = link.get_text(strip=True) or (link.find('img').get('alt', '') if link.find('img') else "Producto Sin Nombre")
                if len(nombre) > 15:
                    asins_vistos.add(asin)
                    # Agregamos a la lista local
                    lista_para_make.append({
                        "producto": nombre[:120],
                        "link": f"https://www.amazon.com/dp/{asin}?tag={AMAZON_TAG}"
                    })

        if lista_para_make:
            # ENVIAMOS LA LISTA COMPLETA EN UNA SOLA PETICIÓN
            res = requests.post(MAKE_WEBHOOK_URL, json={"productos": lista_para_make}, timeout=30)
            if res.status_code == 200:
                enviar_telegram(f"✅ *CHM:* Se enviaron {len(lista_para_make)} productos en un solo paquete a Make.")
        else:
            enviar_telegram("⚠️ No se encontraron productos. Revisa la conexión.")

    except Exception as e:
        enviar_telegram(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
