import requests
from bs4 import BeautifulSoup
import os
import time
import random

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

def rastrear_amazon_agresivo():
    """Buscador de alto rendimiento para asegurar 10 productos."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/'
    }
    
    try:
        response = requests.get(AMAZON_URL, headers=headers, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscamos todos los contenedores posibles (Amazon usa varios diseños)
        items = soup.find_all('div', id='gridItemRoot') or soup.select('div.p13n-grid-col') or soup.select('li.zg-item-immersion')
        
        productos_fisicos = []
        # Lista negra para evitar lo que no quieres vender en Maryland
        blacklist = ["plan", "subscription", "auto-renewal", "gift card", "digital", "membership", "blink", "cloud", "trial"]
        
        for item in items:
            if len(productos_fisicos) >= 10: break
            
            # Buscamos nombre y link con selectores de respaldo
            nombre_tag = item.find('h2') or item.select_one('div._cDE31_p13n-sc-css-line-clamp-3_2A69A')
            link_tag = item.find('a', class_='a-link-normal')
            
            if nombre_tag and link_tag:
                nombre = nombre_tag.get_text(strip=True)
                
                # Filtro de seguridad
                if any(word in nombre.lower() for word in blacklist):
                    continue

                asin_path = link_tag.get('href').split('?')[0]
                link_final = f"https://www.amazon.com{asin_path}?tag={AMAZON_TAG}"
                
                productos_fisicos.append({"producto": nombre, "link": link_final})
        
        return productos_fisicos
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    print("🔎 Iniciando carga de inventario para CHM Brand...")
    lista = rastrear_amazon_agresivo()
    
    if not lista:
        enviar_telegram("⚠️ No se encontraron productos. Revisa los selectores.")
    else:
        enviados = 0
        for p in lista:
            try:
                # Enviamos cada producto individualmente para generar 10 filas
                r = requests.post(MAKE_WEBHOOK_URL, json=p, timeout=20)
                if r.status_code == 200:
                    enviados += 1
                    # Pausa humana para evitar bloqueos de Amazon y Google Sheets
                    time.sleep(random.randint(10, 15)) 
            except:
                continue
        
        enviar_telegram(f"✅ *¡Éxito CHM Brand!* Se registraron {enviados} productos reales en tu Excel.")
