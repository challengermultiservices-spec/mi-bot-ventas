import requests
from bs4 import BeautifulSoup
import os
import json
import time
from fake_useragent import UserAgent

# ==========================================
# CONFIGURACIÓN
# ==========================================

# 1. TUS CREDENCIALES
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
AMAZON_TAG = "chmbrand-20"  # Tu código de afiliado

# 2. CONEXIÓN CON MAKE (¡AQUÍ PEGAS TU WEBHOOK!)
# Este link te lo da el primer módulo de Make (Webhooks > Custom Webhook)
MAKE_WEBHOOK_URL = "https://hook.us1.make.com/TU_CODIGO_SECRETO_AQUI" 

# 3. URL A RASTREAR (Ej: Best Sellers Electrónica)
AMAZON_URL = "https://www.amazon.com/gp/bestsellers/electronics/"

# ==========================================
# HERRAMIENTAS
# ==========================================

def enviar_telegram(mensaje):
    """Envía notificaciones a tu celular"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ No hay credenciales de Telegram configuradas.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error Telegram: {e}")

def obtener_producto_top_1():
    """El Cazador: Entra a Amazon y saca el #1"""
    print(f"🕵️‍♂️ Rastreando Amazon: {AMAZON_URL}")
    
    # Usamos un Agente falso para parecer un humano navegando en Chrome
    ua = UserAgent()
    headers = {
        'User-Agent': ua.random,
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    try:
        response = requests.get(AMAZON_URL, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return None, f"Amazon bloqueó la conexión (Status {response.status_code})"

        soup = BeautifulSoup(response.content, 'lxml')
        
        # BUSCANDO EL PRODUCTO #1
        # Amazon cambia el código a veces, buscamos el contenedor del primer item
        # Usualmente es #gridItemRoot en la nueva vista de Grid
        producto = soup.select_one('#gridItemRoot') or soup.select_one('.zg-item-immersion')

        if not producto:
            return None, "No se encontró la estructura de productos en Amazon (Posible cambio de diseño)."

        # 1. EXTRAER NOMBRE
        nombre_tag = producto.select_one('div > a:nth-of-type(2) > span > div') or \
                     producto.select_one('.p13n-sc-truncate') or \
                     producto.select_one('img')
        
        nombre = nombre_tag.get_text(strip=True) if nombre_tag else "Producto Top 1"
        # Si agarró texto vacío, intentamos con el alt de la imagen
        if len(nombre) < 3 and producto.select_one('img'):
            nombre = producto.select_one('img').get('alt')

        # 2. EXTRAER IMAGEN
        img_tag = producto.select_one('img')
        imagen_url = img_tag.get('src') if img_tag else None

        # 3. EXTRAER LINK Y PONER AFILIADO
        link_tag = producto.select_one('a.a-link-normal')
        link_crudo = link_tag.get('href') if link_tag else None
        
        link_final = "https://www.amazon.com"
        if link_crudo:
            if not link_crudo.startswith('http'):
                link_final += link_crudo
            else:
                link_final = link_crudo
            
            # Añadir tu tag de afiliado
            if "?" in link_final:
                link_final += f"&tag={AMAZON_TAG}"
            else:
                link_final += f"?tag={AMAZON_TAG}"

        if nombre and imagen_url:
            return {
                "producto": nombre,
                "imagen": imagen_url,
                "link": link_final
            }, None
        else:
            return None, "Datos incompletos (Falta nombre o imagen)"

    except Exception as e:
        return None, f"Error de Scraper: {str(e)}"

# ==========================================
# EJECUCIÓN PRINCIPAL
# ==========================================

if __name__ == "__main__":
    print("🚀 Iniciando Protocolo Amazon-Make...")
    
    datos, error = obtener_producto_top_1()

    if error:
        print(f"❌ {error}")
        enviar_telegram(f"❌ *Fallo en Scraper Amazon:*\n{error}")
        exit(1)

    print(f"✅ Producto Encontrado: {datos['producto']}")

    # ENVIAR A MAKE.COM
    if "hook.us1.make.com" in MAKE_WEBHOOK_URL:
        try:
            r = requests.post(MAKE_WEBHOOK_URL, json=datos)
            if r.status_code == 200:
                print("✅ Datos enviados a Make correctamente.")
                enviar_telegram(f"🚀 *Nuevo Top 1 Detectado*\n\n📦 {datos['producto']}\n\n📡 Enviado a Make para crear video.")
            else:
                print(f"⚠️ Make respondió error: {r.text}")
                enviar_telegram(f"⚠️ Make recibió los datos pero dio error: {r.status_code}")
        except Exception as e:
            print(f"❌ Error conectando con Make: {e}")
            enviar_telegram(f"❌ Error fatal conectando con Make: {e}")
    else:
        print("⚠️ No se enviaron datos. FALTA CONFIGURAR LA URL DE MAKE EN bot.py")
        enviar_telegram(f"⚠️ *Falta Configuración:*\nProducto detectado ({datos['producto']}) pero no tengo la URL de Make para enviarlo.")
