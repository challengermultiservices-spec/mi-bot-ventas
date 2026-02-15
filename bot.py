import requests
from bs4 import BeautifulSoup
import os
import time

# ==========================================
# CONFIGURACIÓN PROFESIONAL CHM BRAND
# ==========================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
AMAZON_TAG = "chmbrand-20"
MAKE_WEBHOOK_URL = "https://hook.us2.make.com/iqydw7yi7jr9qwqpmad5vff1gejz2pbh"

# Categoría de Gadgets de Electrónica (Alta rotación para TikTok y Maryland)
AMAZON_URL = "https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics/"

def enviar_telegram(mensaje):
    """Envía actualizaciones de estado directamente a tu celular."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def rastrear_amazon_top_10():
    """Busca los 10 productos más vendidos evitando suscripciones o errores de diseño."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/'
    }
    try:
        response = requests.get(AMAZON_URL, headers=headers, timeout=20)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Selectores universales para la estructura de Amazon 2026
        items = soup.select('div#gridItemRoot')
        if not items:
            items = soup.select('li.zg-item-immersion')

        productos_encontrados = []
        for item in items:
            if len(productos_encontrados) >= 10: break
            
            # Búsqueda multietiqueta del nombre para evitar el "Producto sin nombre"
            nombre_tag = item.select_one('h2 span')
            if not nombre_tag:
                nombre_tag = item.select_one('div._cDE31_p13n-sc-css-line-clamp-3_2A69A')
            if not nombre_tag:
                nombre_tag = item.select_one('span.a-truncate-full')
            
            nombre = nombre_tag.get_text(strip=True) if nombre_tag else "Gadget Tecnológico Viral"
            
            # FILTRO CHM BRAND: Solo productos físicos reales
            if any(x in nombre.lower() for x in ["subscription", "gift card", "digital", "membership", "blink"]):
                continue

            link_tag = item.find('a', class_='a-link-normal')
            img_tag = item.find('img')

            if link_tag and img_tag:
                # Limpiamos el link y añadimos tu tag de afiliado
                link_raw = "https://www.amazon.com" + link_tag.get('href').split('?')[0]
                productos_encontrados.append({
                    "producto": nombre,
                    "imagen": img_tag.get('src'),
                    "link": f"{link_raw}?tag={AMAZON_TAG}"
                })
        return productos_encontrados, None
    except Exception as e:
        return [], str(e)

if __name__ == "__main__":
    print("🔎 CHM Brand: Escaneando tendencias en Amazon...")
    lista, error = rastrear_amazon_top_10()
    
    if not lista:
        enviar_telegram(f"⚠️ *Alerta:* Amazon cambió el diseño o bloqueó el acceso. Error: {error}")
    else:
        enviados = 0
        for p in lista:
            # Enviamos cada producto a Make aprovechando tu nuevo plan de pago
            try:
                r = requests.post(MAKE_WEBHOOK_URL, json=p, timeout=15)
                if r.status_code == 200:
                    enviados += 1
                    # Pausa de 10 seg para asegurar el registro en Google Sheets y Telegram
                    time.sleep(10) 
            except Exception as ex:
                print(f"Error enviando producto: {ex}")
        
        enviar_telegram(f"✅ *¡Operación Exitosa!* Se procesaron {enviados} productos reales para CHM Brand.")
