import requests
from bs4 import BeautifulSoup
import os
import time
import random

# ==========================================
# CONFIGURACIÓN ELITE CHM BRAND - USA TOTAL
# ==========================================
SCRAPER_API_KEY = os.getenv('SCRAPERAPI_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
AMAZON_TAG = "chmbrand-20"
MAKE_WEBHOOK_URL = "https://hook.us2.make.com/iqydw7yi7jr9qwqpmad5vff1gejz2pbh"

def enviar_telegram(mensaje):
    """Envía el estado de la misión a tu celular."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def obtener_productos_con_escudo():
    """Usa ScraperAPI para entrar a Amazon sin ser detectado."""
    target_url = "https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics/"
    
    # El escudo: Pasamos por ScraperAPI con renderizado de JavaScript activo
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}&render=true&country_code=us"
    
    try:
        print("🛡️ CHM Brand: Atravesando el muro de Amazon con Proxy...")
        response = requests.get(proxy_url, timeout=60)
        
        if response.status_code != 200:
            return [], f"Error de acceso (Código {response.status_code}). Revisa tu API Key."

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Selectores de productos físicos
        items = soup.select('div#gridItemRoot') or soup.select('li.zg-item-immersion')
        
        productos_finales = []
        # Lista negra para evitar basura digital
        blacklist = ["plan", "subscription", "auto-renewal", "gift card", "digital", "membership", "blink", "cloud", "trial"]
        
        for item in items:
            if len(productos_finales) >= 10: break
            
            nombre_tag = item.find('h2') or item.select_one('div._cDE31_p13n-sc-css-line-clamp-3_2A69A')
            link_tag = item.find('a', class_='a-link-normal')
            
            if nombre_tag and link_tag:
                nombre = nombre_tag.get_text(strip=True)
                
                # Filtro de seguridad: Solo lo que se puede tocar y vender
                if any(word in nombre.lower() for word in blacklist):
                    continue

                asin_path = link_tag.get('href').split('?')[0]
                link_final = f"https://www.amazon.com{asin_path}?tag={AMAZON_TAG}"
                
                productos_finales.append({
                    "producto": nombre[:110],
                    "link": link_final
                })
        
        return productos_finales, None
    except Exception as e:
        return [], str(e)

if __name__ == "__main__":
    print("🚀 Iniciando motor de búsqueda USA...")
    lista, error = obtener_productos_con_escudo()
    
    if not lista:
        enviar_telegram(f"❌ *CHM Report:* No se pudo romper el bloqueo. {error}")
    else:
        exitos = 0
        for p in lista:
            try:
                # Enviamos cada producto individual para crear las 10 filas
                r = requests.post(MAKE_WEBHOOK_URL, json=p, timeout=20)
                if r.status_code == 200:
                    exitos += 1
                    # Pausa de 8 segundos: suficiente con el proxy activo
                    time.sleep(8) 
            except:
                continue
        
        enviar_telegram(f"✅ *¡Misión Cumplida!* Se inyectaron {exitos} productos reales de USA en tu inventario.")
