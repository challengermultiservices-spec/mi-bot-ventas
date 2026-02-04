import os, requests, json, gspread, time, random, sys, re
from google.oauth2.service_account import Credentials
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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

    # Configurar Sesión con Reintentos a nivel de Protocolo
    session = requests.Session()
    retry_strategy = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0 Safari/537.36"})

    print("🚀 Iniciando Bot con Sesión Reforzada...")

    try:
        # 1. Google Sheets
        creds = Credentials.from_service_account_info(json.loads(creds_raw), 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        sheet = gspread.authorize(creds).open_by_key(ID_HOJA).get_worksheet(0)
        print("✅ Sheets Conectado")

       # 2. Gemini
        url_g = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
        prompt = "Suggest 1 Amazon gadget. Return ONLY JSON: {\"prod\": \"Name\", \"hook\": \"Hook\", \"body\": \"Body\"}"
        r_g = session.post(url_g, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        datos = json.loads(re.search(r'\{.*\}', r_g.text, re.DOTALL).group(0))
        prod_nombre = datos.get('prod', 'Gadget')

        # 3. Creatomate (Paso Crítico)
        print("🚀 Enviando a Creatomate...")
        u_c = "https://api.creatomate.com/v2/renders"
        h_c = {"Authorization": f"Bearer {creatomate_key}", "Content-Type": "application/json"}
        payload = {
            "template_id": TEMPLATE_ID,
            "modifications": {
                "Text-1.text": datos.get('hook', 'AMAZON FIND').upper(),
                "Text-2.text": datos.get('body', '')
            }
        }

        # Intentar el renderizado con la sesión reforzada
        res_c = session.post(u_c, headers=h_c, json=payload, timeout=60)
        if res_c.status_code not in [200, 201, 202]:
            raise Exception(f"Error {res_c.status_code}: {res_c.text}")
        
        render_id = res_c.json()[0]['id']
        video_url = res_c.json()[0]['url']

        # 4. Espera Activa
        print("⏳ Procesando video...")
        for _ in range(10):
            time.sleep(20)
            check = session.get(f"https://api.creatomate.com/v2/renders/{render_id}", headers=h_c, timeout=30).json()
            if check.get('status') == 'succeeded':
                print("✅ Video terminado")
                break

        # 5. Registro y Notificación
        l_amz = f"https://www.amazon.com/s?k={prod_nombre.replace(' ', '+')}&tag={AMAZON_TAG}"
        sheet.append_row([prod_nombre, l_amz, video_url])
        
        msg = f"🎬 *¡Video Listo!*\n\n📦 *Producto:* {prod_nombre}\n🎥 [Ver Video]({video_url})\n🛒 [Amazon]({l_amz})"
        enviar_telegram(msg)
        print("🏁 PROCESO COMPLETADO")

    except Exception as e:
        error_msg = f"❌ *Error en el Bot:* {str(e)}"
        enviar_telegram(error_info := error_msg)
        print(error_info)
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_bot()
