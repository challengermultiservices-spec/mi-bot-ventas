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

def obtener_productos():
    # Rotamos la identidad del bot para que parezca un humano real
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    ]
    
    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/'
    }

    try:
        session = requests.Session()
        response = session.get(AMAZON_URL, headers=headers, timeout=30)
        
        if "captcha" in response.text.lower():
            return [], "🚫 Amazon bloqueó la IP. Intentando saltar..."
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # BUSCADOR POR ADN (Patrón ASIN de 10 caracteres)
        # Esto es lo más difícil de ocultar para Amazon
        enlaces = soup.find_all('a', href=re.compile(r'\/dp\/[A-Z0-9]{10}'))
        
        resultados = []
        vistos = set()
        blacklist = ["plan", "subscription", "gift card", "digital", "membership", "blink", "cloud", "trial"]

        for link in enlaces:
            if len(resultados) >= 10: break
            
            href = link.get('href')
            asin = re.search(r'\/dp\/([A-Z0-9]{10})', href).group(1)
            
            if asin in vistos: continue
            
            # Buscamos el nombre en el texto o en la imagen del producto
            nombre = link.get_text(strip=True) or (link.find('img').get('alt', '') if link.find('img') else "")
            
            if len(nombre) > 15 and not any(w in nombre.lower() for w in blacklist):
                vistos.add(asin)
                resultados.append({
                    "producto": nombre[:80], # Limitamos largo para Make
                    "link": f"https://www.amazon.com/dp/{asin}?tag={AMAZON_TAG}"
                })
        
        return resultados, None if resultados else "⚠️ Amazon ocultó los productos. Reintentando en la próxima ejecución."

    except Exception as e:
        return [], str(e)

if __name__ == "__main__":
    lista, error = obtener_productos()
    
    if not lista:
        enviar_telegram(f"CHM Brand Report: {error}")
    else:
        enviados = 0
        for p in lista:
            try:
                r = requests.post(MAKE_WEBHOOK_URL, json=p, timeout=20)
                if r.status_code == 200:
                    enviados += 1
                    time.sleep(random.randint(10, 15)) # Pausa para no ser detectados
            except: continue
        
        enviar_telegram(f"✅ *CHM Brand:* ¡Éxito! {enviados} productos nuevos en tu Excel.")
