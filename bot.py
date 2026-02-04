import os, requests, json, gspread, time, random, sys, re
from google.oauth2.service_account import Credentials

def enviar_telegram(mensaje):
    token = os.environ.get("TELEGRAM_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": mensaje, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=10)
    except: pass

def ejecutar_bot():
    # Variables de entorno
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    creatomate_key = os.environ.get("CREATOMATE_API_KEY", "").strip()
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS", "").strip()
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"
    AMAZON_TAG = "chmbrand-20"

    print("🚀 Iniciando Bot con Bypass...")

    try:
        # 1. Google Sheets
        creds = Credentials.from_service_account_info(json.loads(creds_raw), 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        sheet = gspread.authorize(creds).open_by_key(ID_HOJA).get_worksheet(0)
        print("✅ Sheets Conectado")

        # 2. Gemini
        url_g = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
        prompt = "Suggest 1 Amazon gadget. Return ONLY JSON: {\"prod\": \"Name\", \"hook\": \"Hook\", \"body\": \"Body\"}"
        r_g = requests.post(url_g, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        datos = json.loads(re.search(r'\{.*\}', r_g.text, re.DOTALL).group(0))
        prod_nombre = datos.get('prod', 'Gadget')

        # 3. Creatomate (Estrategia de conexión simple)
        print("🚀 Enviando a Creatomate...")
        # Usamos una conexión directa sin sesión compleja para evitar firmas de bot
        h_c = {
            "Authorization": f"Bearer {creatomate_key}",
            "Content-Type": "application/json",
            "Accept": "*/*"
        }
        payload = {
            "template_id": TEMPLATE_ID,
            "modifications": {
                "Text-1.text": datos.get('hook', 'AMAZON FIND').upper(),
                "Text-2.text": datos.get('body', '')
            }
        }

        # Cambiamos el timeout y forzamos el cierre de conexión para limpiar el túnel
        res_c = requests.post(
            "https://api.creatomate.com/v2/renders", 
            headers=h_c, 
            json=payload, 
            timeout=60,
            stream=False # Forzar descarga completa
        )
        
        if res_c.status_code != 200:
            raise Exception(f"API Error {res_c.status_code}")
        
        render_data = res_c.json()
        render_id = render_data[0]['id']
        video_url = render_data[0]['url']

        # 4. Registro y Notificación (Sin esperar al renderizado completo para evitar timeouts)
        l_amz = f"https://www.amazon.com/s?k={prod_nombre.replace(' ', '+')}&tag={AMAZON_TAG}"
        sheet.append_row([prod_nombre, l_amz, video_url])
        
        msg = f"🎬 *¡Video en Proceso!*\n\n📦 *Producto:* {prod_nombre}\n🎥 [Enlace del Video]({video_url})\n🛒 [Link Amazon]({l_amz})\n\n_Nota: Espera 2 min para que el video cargue._"
        enviar_telegram(msg)
        print("🏁 PROCESO COMPLETADO")

    except Exception as e:
        error_msg = f"❌ *Error en el Bot:* {str(e)}"
        enviar_telegram(error_msg)
        print(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_bot()
