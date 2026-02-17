import requests
from bs4 import BeautifulSoup
import os
import time
import random
import re

# ==========================================
# CONFIGURACIÓN CHM BRAND - Maryland
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

def obtener_productos_stealth():
    # Identidades variadas para engañar a Amazon
    u_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    ]
    
    headers = {
        'User-Agent': random.choice(u_agents),
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.google.com/',
        'DNT': '1'
    }

    try:
        session = requests.Session()
        # Simulamos una visita a la home primero para "calentar" la sesión
        session.get("https://www.amazon.com", headers=headers, timeout=15)
        time.sleep(random.uniform(2, 5))
        
        response = session.get(AMAZON_URL, headers=headers, timeout=30)
        
        if "captcha" in response.text.lower():
            return [], "🚫 Amazon activó un CAPTCHA. La IP de GitHub está marcada."
            
        soup = BeautifulSoup(response.content, 'html.parser')
        # Buscamos enlaces de productos por patrón ASIN
        enlaces = soup.find_all('a', href=re.compile(r'\/dp\/[A-Z0-9]{10}'))
        
        resultados = []
        asins_vistos = set()
        blacklist = ["plan", "subscription", "gift card", "digital", "membership", "blink", "cloud", "trial"]

        for link in enlaces:
            if len(resultados) >= 10: break
            
            href = link.get('href')
            match = re.search(r'\/dp\/([A-Z0-9]{10})', href)
            if not match: continue
            asin = match.group(1)
            
            if asin in asins_vistos: continue
            
            # Buscamos el nombre con prioridad en el texto limpio
            nombre = link.get_text(strip=True)
            if not nombre or len(nombre) < 10:
                img = link.find('img')
                nombre = img.get('alt', '') if img else ""

            if len(nombre) > 15 and not any(w in nombre.lower() for w in blacklist):
                asins_vistos.add(asin)
                resultados.append({
                    "producto": nombre[:100], 
                    "link": f"https://www.amazon.com/dp/{asin}?tag={AMAZON_TAG}"
                })
        
        return resultados, None if resultados else "⚠️ Página cargada pero no se detectaron productos físicos."

    except Exception as e:
        return [], f"Error de conexión: {str(e)}"

if __name__ == "__main__":
    print("🚀 Iniciando misión secreta CHM Brand...")
    lista, error = obtener_productos_stealth()
    
    if not lista:
        enviar_telegram(f"Reporte CHM: {error}")
    else:
        exitos = 0
        for p in lista:
            try:
                # El envío a Make debe ser lento para que Google Sheets no se trabe
                r = requests.post(MAKE_WEBHOOK_URL, json=p, timeout=20)
                if r.status_code == 200:
                    exitos += 1
                    # Pausa larga y aleatoria: Vital para Maryland
                    time.sleep(random.randint(15, 25)) 
            except: continue
        
        enviar_telegram(f"✅ *CHM Brand:* Se han inyectado {exitos} productos reales en tu inventario.")
