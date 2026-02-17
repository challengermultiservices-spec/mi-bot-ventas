import requests
from bs4 import BeautifulSoup
import os
import time
import random
import re

# ==========================================
# CONFIGURACIÓN ELITE - CHM BRAND
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

def rastreo_elite():
    """Rastreador con rotación de cabeceras y validación de duplicados."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/',
        'Viewport-Width': '1920'
    }

    try:
        session = requests.Session()
        # "Calentamos" la sesión como si fuera un usuario real
        session.get("https://www.amazon.com", headers=headers, timeout=15)
        time.sleep(random.uniform(1, 3))
        
        response = session.get(AMAZON_URL, headers=headers, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscamos todos los enlaces con patrón de producto (/dp/)
        enlaces_crudos = soup.find_all('a', href=re.compile(r'\/dp\/[A-Z0-9]{10}'))
        
        inventario_10 = []
        asins_registrados = set()
        # Filtro de seguridad CHM
        blacklist = ["plan", "subscription", "gift card", "digital", "membership", "blink", "cloud", "auto-renewal"]

        for link in enlaces_crudos:
            if len(inventario_10) >= 10: break
            
            href = link.get('href')
            asin = re.search(r'\/dp\/([A-Z0-9]{10})', href).group(1)
            
            # EVITAMOS REPETIDOS (Solución a lo visto en image_3ee5e0.png)
            if asin in asins_registrados: continue
            
            nombre = link.get_text(strip=True) or (link.find('img').get('alt', '') if link.find('img') else "")
            
            if len(nombre) > 20 and not any(b in nombre.lower() for b in blacklist):
                asins_registrados.add(asin)
                inventario_10.append({
                    "producto": nombre[:120],
                    "link": f"https://www.amazon.com/dp/{asin}?tag={AMAZON_TAG}"
                })
        
        return inventario_10, None
    except Exception as e:
        return [], str(e)

if __name__ == "__main__":
    print("🚀 CHM Brand: Iniciando barrido de inventario...")
    lista, error = rastreo_elite()
    
    if not lista:
        enviar_telegram(f"❌ Reporte CHM: Amazon bloqueó la vista. Detalle: {error}")
    else:
        procesados = 0
        for p in lista:
            try:
                # Envío individual para forzar las 10 filas
                r = requests.post(MAKE_WEBHOOK_URL, json=p, timeout=20)
                if r.status_code == 200:
                    procesados += 1
                    # PAUSA CRÍTICA: Evita que Amazon detecte el flujo de datos masivo
                    time.sleep(random.randint(20, 35)) 
            except: continue
        
        enviar_telegram(f"✅ *CHM Brand:* Se han inyectado {procesados} productos únicos en Maryland.")
