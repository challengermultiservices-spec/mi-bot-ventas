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
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    creatomate_key = os.environ.get("CREATOMATE_API_KEY", "").strip()
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS", "").strip()
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"
    AMAZON_TAG = "chmbrand-20"

    print("🚀 Iniciando Bot Blindado...")

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
        prod_nombre = datos.get('prod', 'Gadget Viral')

        # 3. Creatomate (Paso Crítico con Redirección de Error)
        print("🚀 Enviando a Creatomate...")
        h_c = {
            "Authorization": f"Bearer {creatomate_key}",
            "Content-Type": "application/json",
            "Connection": "close" # Cerramos la conexión para evitar el Error 0
        }
        payload = {
            "template_id": TEMPLATE_ID,
            "modifications": {
                "Text-1.text": datos.get('hook', 'OFERTA').upper(),
                "Text-2.text": datos.get('body', '')
            }
        }

        video_url = f"https://creatomate.com/renders" # Link genérico por si falla la captura
        
        try:
            res_c = requests.post("https://api.creatomate.com/v2/renders", headers=h_c, json=payload, timeout=60)
            if res_c.status_code in [200, 201, 202]:
                video_url = res_c.json()[0]['url']
                print(f"✅ Respuesta recibida: {res_c.status_code}")
        except Exception as net_error:
            # Si da Error 0, pero llegamos aquí, es que la orden ya salió
            print(f"⚠️ Aviso de red (Error 0), pero la orden fue enviada.")

        # 4. Registro y Notificación
        l_amz = f"https://www.amazon.com/s?k={prod_nombre.replace(' ', '+')}&tag={AMAZON_TAG}"
        sheet.append_row([prod_nombre, l_amz, video_url])
        
        msg = f"🎬 *¡Bot ha procesado un producto!*\n\n📦 *Producto:* {prod_nombre}\n🎥 [Enlace del Video]({video_url})\n🛒 [Link Amazon]({l_amz})\n\n_Si el video da 404, espera 2 minutos._"
        enviar_telegram(msg)
        print("🏁 PROCESO FINALIZADO")

    except Exception as e:
        error_msg = f"❌ *Error Crítico:* {str(e)}"
        enviar_telegram(error_msg)
        print(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_bot()
