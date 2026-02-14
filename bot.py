import requests
from bs4 import BeautifulSoup
import os
import json
import time
from fake_useragent import UserAgent

# ==========================================
# CONFIGURACIÓN
# ==========================================

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
AMAZON_TAG = "chmbrand-20" 

# ¡¡¡PEGA AQUÍ TU WEBHOOK DE MAKE!!! (Sin espacios extra)
MAKE_WEBHOOK_URL = "TU_LINK_DE_MAKE_AQUI" 

# Usaremos una categoría específica que suele ser más estable
AMAZON_URL = "https://www.amazon.com/gp/bestsellers/electronics/"

# ==========================================
# FUNCIONES
# ==========================================

def enviar_telegram(mensaje):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except: pass

def obtener_producto_top_1():
    print(f"🕵️‍♂️ Rastreando Amazon: {AMAZON_URL}")
    
    ua = UserAgent()
    # Cabeceras rotativas para despistar a Amazon
    headers = {
        'User-Agent': ua.random,
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Referer': 'https://www.google.com/',
        'DNT': '1', # Do Not Track
        'Upgrade-Insecure-Requests': '1'
    }

    try:
        response = requests.get(AMAZON_URL, headers=headers, timeout=20)
        
        if response.status_code != 200:
            return None, f"Amazon bloqueó la conexión (Status {response.status_code})"

        soup = BeautifulSoup(response.content, 'lxml')
        
        # --- ESTRATEGIA MULTI-VISIÓN ---
        
        # Intento 1: El ID estándar del primer producto (#p13n-asin-index-0)
        producto = soup.select_one('#p13n-asin-index-0')
        
        # Intento 2: Buscar por la clase de la tarjeta (zg-grid-general-faceout)
        if not producto:
            tarjetas = soup.select('.zg-grid-general-faceout')
            if tarjetas: producto = tarjetas[0]
            
        # Intento 3: Buscar cualquier imagen dentro del área de contenido principal
        if not producto:
            producto = soup.select_one('.a-cardui img')
            if producto: producto = producto.find_parent('div', class_='a-cardui')

        if not producto:
            # Si falla todo, guardamos un pedacito del HTML para ver qué pasó
            debug_html = str(soup.body)[:500] 
            return None, f"No se encontró estructura. HTML parcial: {debug_html}"

        # --- EXTRACCIÓN DE DATOS ---
        
        # 1. Nombre
        nombre = "Producto Top 1"
        img_tag = producto.select_one('img')
        link_tag = producto.select_one('a.a-link-normal')
        
        if img_tag and img_tag.get('alt'):
            nombre = img_tag.get('alt')
        elif link_tag:
            nombre = link_tag.get_text(strip=True)

        # 2. Imagen
        imagen_url = img_tag.get('src') if img_tag else None

        # 3. Link
        link_final = "https://www.amazon.com"
        if link_tag:
            href = link_tag.get('href')
            if href:
                if not href.startswith('http'): link_final += href
                else: link_final = href
                
                # Agregar Afiliado
                sep = "&" if "?" in link_final else "?"
                link_final += f"{sep}tag={AMAZON_TAG}"

        if nombre and imagen_url:
            return {
                "producto": nombre,
                "imagen": imagen_url,
                "link": link_final
            }, None
        else:
            return None, "Datos incompletos (Falta nombre o imagen)"

    except Exception as e:
        return None, f"Error interno: {str(e)}"

# ==========================================
# EJECUCIÓN
# ==========================================

if __name__ == "__main__":
    datos, error = obtener_producto_top_1()

    if error:
        print(f"❌ {error}")
        enviar_telegram(f"❌ *Fallo Scraper:* {error}")
        exit(1)

    print(f"✅ ÉXITO: {datos['producto']}")
    
    # ENVIAR A MAKE
    if "hook.us1.make.com" in MAKE_WEBHOOK_URL:
        try:
            r = requests.post(MAKE_WEBHOOK_URL, json=datos)
            if r.status_code == 200:
                print("✅ Enviado a Make.")
                enviar_telegram(f"🚀 *Producto Detectado:*\n{datos['producto']}\n\n📡 Enviado a Make.")
            else:
                print(f"⚠️ Error Make: {r.status_code}")
                enviar_telegram(f"⚠️ Error Make: {r.status_code}")
        except Exception as e:
            print(f"❌ Error conexión: {e}")
    else:
        print("⚠️ URL de Make no configurada o incorrecta.")
        enviar_telegram(f"⚠️ *Falta URL Make:*\nProducto: {datos['producto']}")
