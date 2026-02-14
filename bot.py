import requests
from bs4 import BeautifulSoup
import os
import time
import random

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================

# El robot lee las llaves de los "Secrets" de GitHub
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
AMAZON_TAG = "chmbrand-20"

# ✅ TU WEBHOOK DE MAKE (Ya configurado)
MAKE_WEBHOOK_URL = "https://hook.us2.make.com/5f3gdsmz7oob77i6qorrsiqppb8sfdnw"

AMAZON_URL = "https://www.amazon.com/gp/bestsellers/electronics/"

# ==========================================
# 2. FUNCIONES
# ==========================================

def enviar_telegram(mensaje):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except: pass

def rastrear_amazon():
    # MÁSCARA DE WINDOWS 10 (PC) PARA EVITAR ERRORES
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Referer': 'https://www.google.com/',
        'DNT': '1'
    }

    try:
        response = requests.get(AMAZON_URL, headers=headers, timeout=20)
        
        if response.status_code != 200:
            return None, f"Status Code: {response.status_code}"

        soup = BeautifulSoup(response.content, 'lxml')

        if "captcha" in soup.text.lower():
            return None, "Amazon pide Captcha (Bloqueo temporal)"

        # ESTRATEGIA DE BÚSQUEDA (PC)
        producto = soup.select_one('#gridItemRoot') # Grid moderno
        if not producto: producto = soup.select_one('.zg-item-immersion') # Lista vieja
        if not producto: producto = soup.select_one('div[class*="zg-grid-general-faceout"]') # Genérico

        if not producto:
            return None, "No se encontró producto (HTML desconocido en modo PC)"

        # EXTRACCIÓN
        img = producto.select_one('img')
        link = producto.select_one('a.a-link-normal')
        
        nombre = "Top 1 Amazon"
        if img and img.get('alt'): nombre = img.get('alt')
        elif link: nombre = link.get_text(strip=True)

        imagen_url = img.get('src') if img else None
        # Truco de calidad de imagen
        if imagen_url and "._AC" in imagen_url:
             imagen_url = imagen_url.split("._AC")[0] + "._AC_SL1000_.jpg"

        link_final = "https://www.amazon.com"
        if link:
            href = link.get('href')
            if href:
                base = href if href.startswith('http') else "https://www.amazon.com" + href
                sep = "&" if "?" in base else "?"
                link_final = f"{base}{sep}tag={AMAZON_TAG}"

        if nombre and imagen_url:
            return {"producto": nombre, "imagen": imagen_url, "link": link_final}, None
        
        return None, "Faltó imagen o nombre"

    except Exception as e:
        return None, f"Error Python: {str(e)}"

# ==========================================
# 3. EJECUCIÓN
# ==========================================

if __name__ == "__main__":
    print("🚀 Iniciando Bot con Make...")

    for i in range(3):
        print(f"🔄 Intento {i+1}...")
        datos, error = rastrear_amazon()
        
        if datos:
            print(f"✅ ENCONTRADO: {datos['producto']}")
            try:
                # ENVIAR A MAKE
                r = requests.post(MAKE_WEBHOOK_URL, json=datos)
                
                if r.status_code == 200:
                    msg = f"🚀 *¡Éxito Total!*\n\n📦 *Producto:* {datos['producto']}\n✅ Enviado a Make para crear video."
                    enviar_telegram(msg)
                    print("✅ Enviado a Make Correctamente.")
                    exit(0) # Terminamos con éxito
                else:
                    print(f"⚠️ Error Make: {r.status_code} - {r.text}")
                    enviar_telegram(f"⚠️ Make dio error: {r.status_code}")
            except Exception as e:
                print(f"❌ Error de Conexión: {e}")
            break 
        
        print(f"⚠️ Fallo Amazon: {error}")
        time.sleep(5)
    
    if error:
        enviar_telegram(f"❌ Fallaron los 3 intentos en Amazon. Error: {error}")
        exit(1)
