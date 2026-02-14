import requests
from bs4 import BeautifulSoup
import os
import json
import time
import random
from fake_useragent import UserAgent

# ==========================================
# 1. CONFIGURACIÓN (¡Revisa esto!)
# ==========================================

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
AMAZON_TAG = "chmbrand-20" 

# 👇👇👇 ¡AQUÍ ES DONDE ESTÁ EL ERROR 404! 👇👇👇
# Asegúrate de copiar TODO el enlace desde Make.com
MAKE_WEBHOOK_URL = "https://hook.us1.make.com/TU_CODIGO_REAL_AQUI" 

AMAZON_URL = "https://www.amazon.com/gp/bestsellers/electronics/"

# ==========================================
# 2. HERRAMIENTAS
# ==========================================

def enviar_telegram(mensaje):
    """Envía notificaciones a Telegram"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except: pass

def obtener_producto_con_reintentos():
    """Intenta 3 veces por si Amazon nos bloquea"""
    intentos = 3
    for i in range(intentos):
        print(f"🔄 Intento {i+1} de {intentos}...")
        datos, error = rastrear_amazon()
        
        if datos:
            return datos, None # ¡Éxito!
        
        # Si falló, esperamos un tiempo aleatorio (5 a 10 seg)
        print(f"⚠️ Fallo intento {i+1}. Esperando para reintentar...")
        time.sleep(random.uniform(5, 10))
    
    return None, "Amazon bloqueó los 3 intentos. Revisa GitHub Actions más tarde."

def rastrear_amazon():
    ua = UserAgent()
    headers = {
        'User-Agent': ua.random,
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

        # Detección de Bloqueo (Captcha)
        if "captcha" in soup.text.lower() or "robot check" in soup.title.text.lower():
            return None, "Amazon detectó Robot (Captcha)"

        # Búsqueda del producto (Estrategia Mixta)
        producto = soup.select_one('#gridItemRoot') or \
                   soup.select_one('.zg-item-immersion') or \
                   soup.select_one('.zg-grid-general-faceout')

        if not producto:
            # Debug: Ver si cargó algo raro
            return None, "Estructura HTML no reconocida (Posible cambio de diseño o bloqueo suave)"

        # Extracción de datos
        img_tag = producto.select_one('img')
        link_tag = producto.select_one('a.a-link-normal')
        
        # Nombre
        nombre = "Producto Top 1"
        if img_tag and img_tag.get('alt'): nombre = img_tag.get('alt')
        elif link_tag: nombre = link_tag.get_text(strip=True)

        # Imagen
        imagen_url = img_tag.get('src') if img_tag else None

        # Link
        link_final = "https://www.amazon.com"
        if link_tag:
            href = link_tag.get('href')
            if href:
                link_final = ("https://www.amazon.com" + href) if not href.startswith('http') else href
                sep = "&" if "?" in link_final else "?"
                link_final += f"{sep}tag={AMAZON_TAG}"

        if nombre and imagen_url:
            return {"producto": nombre, "imagen": imagen_url, "link": link_final}, None
        
        return None, "Datos incompletos en el HTML"

    except Exception as e:
        return None, f"Error técnico: {str(e)}"

# ==========================================
# 3. EJECUCIÓN PRINCIPAL
# ==========================================

if __name__ == "__main__":
    print("🚀 Iniciando Bot Challenger...")
    
    datos, error = obtener_producto_con_reintentos()

    if error:
        print(f"❌ {error}")
        enviar_telegram(f"❌ *Fallo Definitivo:* {error}")
        exit(1)

    print(f"✅ PRODUCTO ENCONTRADO: {datos['producto']}")
    
    # ENVIAR A MAKE (Crítico)
    # Validamos que la URL no sea la de ejemplo
    if "TU_CODIGO_REAL" in MAKE_WEBHOOK_URL or "make.com" not in MAKE_WEBHOOK_URL:
        msg = "⚠️ *ERROR DE CONFIGURACIÓN:* La URL de Make en bot.py es incorrecta."
        print(msg)
        enviar_telegram(msg)
        exit(1)

    try:
        print(f"📡 Enviando a Make: {MAKE_WEBHOOK_URL}")
        r = requests.post(MAKE_WEBHOOK_URL, json=datos)
        
        if r.status_code == 200:
            print("✅ ÉXITO TOTAL: Datos entregados a Make.")
            enviar_telegram(f"🚀 *¡Ciclo Completado!*\n\n📦 {datos['producto']}\n📡 Enviado a Make para video.")
        elif r.status_code == 404:
            msg = "❌ Error 404 en Make: La URL del Webhook no existe. Cópiala de nuevo."
            print(msg)
            enviar_telegram(msg)
        else:
            print(f"⚠️ Make respondió: {r.status_code}")
            enviar_telegram(f"⚠️ Make recibió pero dio error: {r.status_code}")
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        enviar_telegram(f"❌ Error conectando a Make: {e}")
