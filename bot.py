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
    """Buscador de fuerza bruta que rastrea cualquier patrón de producto."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        response = requests.get(AMAZON_URL, headers=headers, timeout=30)
        if response.status_code != 200:
            return [], f"Amazon rechazó la conexión (Código {response.status_code})"
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # BUSCADOR UNIVERSAL: Buscamos enlaces que contengan '/dp/' (patrón de producto de Amazon)
        all_links = soup.find_all('a', href=re.compile(r'\/dp\/[A-Z0-9]{10}'))
        
        productos_fisicos = []
        enlaces_vistos = set()
        blacklist = ["plan", "subscription", "gift card", "digital", "membership", "blink", "cloud", "trial", "auto-renewal"]
        
        for link in all_links:
            if len(productos_fisicos) >= 10: break
            
            href = link.get('href')
            # Extraemos el ASIN (código único) para evitar repetidos
            asin_match = re.search(r'\/dp\/([A-Z0-9]{10})', href)
            if not asin_match: continue
            asin = asin_match.group(1)
            
            if asin in enlaces_vistos: continue
            
            # Buscamos el nombre: puede estar en el texto del link o en una imagen dentro del link
            nombre = link.get_text(strip=True)
            if not nombre:
                img = link.find('img')
                nombre = img.get('alt', '') if img else ""
            
            # Limpieza y filtrado
            if len(nombre) < 10 or any(word in nombre.lower() for word in blacklist):
                continue

            enlaces_vistos.add(asin)
            link_final = f"https://www.amazon.com/dp/{asin}?tag={AMAZON_TAG}"
            
            productos_fisicos.append({
                "producto": nombre,
                "link": link_final
            })
            
        if not productos_fisicos:
            return [], "Amazon ocultó los productos. Intentando con selectores de imagen..."
            
        return productos_fisicos, None
    except Exception as e:
        return [], str(e)

if __name__ == "__main__":
    print("🔎 CHM Brand: Iniciando rastreo universal...")
    lista, error = rastrear_amazon_universal()
    
    if not lista:
        enviar_telegram(f"⚠️ *Alerta Jorge:* {error}")
    else:
        enviados = 0
        for p in lista:
            try:
                r = requests.post(MAKE_WEBHOOK_URL, json=p, timeout=15)
                if r.status_code == 200:
                    enviados += 1
                    time.sleep(random.randint(5, 8)) 
            except: continue
        
        enviar_telegram(f"✅ *¡Operación Exitosa!* Se enviaron {enviados} productos reales a tu Excel.")
