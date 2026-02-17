import requests
from bs4 import BeautifulSoup
import os
import time
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
    if not SCRAPER_API_KEY:
        enviar_telegram("❌ Error: No se detectó la llave en GitHub.")
        return

    # Usamos ScraperAPI con ultra-renderizado y espera de 5 segundos para que cargue todo
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url=https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics/&render=true&country_code=us&wait_for_selector=.zg-grid-general-faceout"

    try:
        print("🛡️ CHM Brand: Iniciando escaneo profundo...")
        r = requests.get(proxy_url, timeout=120)
        soup = BeautifulSoup(r.content, 'html.parser')

        # Buscamos cualquier link que tenga un código de producto (ASIN)
        enlaces = soup.find_all('a', href=re.compile(r'/(dp|gp/product)/[A-Z0-9]{10}'))
        
        productos_unicos = []
        asins_vistos = set()
        blacklist = ["plan", "subscription", "gift card", "digital", "membership", "blink", "cloud", "trial"]

        for link in enlaces:
            if len(productos_unicos) >= 10: break
            
            href = link.get('href')
            match = re.search(r'/(dp|gp/product)/([A-Z0-9]{10})', href)
            if not match: continue
            
            asin = match.group(2)
            if asin in asins_vistos: continue

            # Extraemos nombre del texto o del atributo de la imagen
            nombre = link.get_text(strip=True) or (link.find('img').get('alt', '') if link.find('img') else "")
            
            if len(nombre) < 15 or any(w in nombre.lower() for w in blacklist):
                continue

            asins_vistos.add(asin)
            productos_unicos.append({"producto": nombre[:120], "link": f"https://www.amazon.com/dp/{asin}?tag={AMAZON_TAG}"})

        if not productos_unicos:
            enviar_telegram("⚠️ No se encontraron productos nuevos hoy. Reintentando...")
            return

        # ENVIAMOS UNO POR UNO CON MENSAJE DE CONFIRMACIÓN
        enviados_con_exito = 0
        for p in productos_unicos:
            try:
                # El tiempo de espera es vital para que Google Sheets no bloquee la fila
                res = requests.post(MAKE_WEBHOOK_URL, json=p, timeout=30)
                if res.status_code == 200:
                    enviados_con_exito += 1
                    # TE AVISARÁ CADA VEZ QUE UNO ENTRE A MAKE
                    print(f"Enviado: {p['producto']}") 
                time.sleep(20) # Pausa larga para asegurar la escritura
            except:
                continue

        enviar_telegram(f"✅ *CHM Final:* Se procesaron {enviados_con_exito} productos diferentes.")

    except Exception as e:
        enviar_telegram(f"❌ Error crítico: {str(e)}")

if __name__ == "__main__":
    main()
