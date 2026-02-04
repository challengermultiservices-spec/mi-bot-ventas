import os, requests, json, gspread, time, random, sys, re
from google.oauth2.service_account import Credentials

def enviar_telegram(mensaje):
    token = os.environ.get("TELEGRAM_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": mensaje, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=10)
    except: print("⚠️ Error en Telegram")

def ejecutar_bot_maestro():
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    creatomate_key = os.environ.get("CREATOMATE_API_KEY", "").strip()
    pexels_key = os.environ.get("PEXELS_API_KEY", "").strip()
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS", "").strip()
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    try:
        # 1. Sheets
        creds = Credentials.from_service_account_info(json.loads(creds_raw), 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        sheet = gspread.authorize(creds).open_by_key(ID_HOJA).get_worksheet(0)
        print("✅ Sheets Conectado")

        # 2. Gemini
        url_g = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
        prompt = "Suggest a viral Amazon gadget. Return ONLY JSON: {\"prod\": \"Name\", \"query\": \"English\", \"hook\": \"Hook\", \"body\": \"Text\"}"
        r_g = requests.post(url_g, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        datos = json.loads(re.search(r'\{.*\}', r_g.text, re.DOTALL).group(0))
        prod_nombre = datos.get('prod', 'Gadget')

        # 3. Pexels
        video_f = "https://creatomate.com/files/assets/7347c3b7-e1a8-4439-96f1-f3dfc95c3d28"
        try:
            p_res = requests.get(f"https://api.pexels.com/videos/search?query={datos['query']}&per_page=1&orientation=portrait", 
                                 headers={"Authorization": pexels_key}, timeout=20)
            if p_res.status_code == 200: video_f = p_res.json()['videos'][0]['video_files'][0]['link']
        except: print("⚠️ Usando fondo por defecto")

        # 4. Creatomate (Con manejo de errores mejorado)
        print("🚀 Enviando a Creatomate...")
        u_c = "https://api.creatomate.com/v2/renders"
        h_c = {"Authorization": f"Bearer {creatomate_key}", "Content-Type": "application/json"}
        payload = {
            "template_id": TEMPLATE_ID,
            "modifications": {
                "Video.source": video_f,
                "Text-1.text": datos.get('hook', 'AMAZON FIND').upper(),
                "Text-2.text": datos.get('body', '')
            }
        }
        
        res_c = requests.post(u_c, headers=h_c, json=payload, timeout=40)
        
        if res_c.status_code not in [200, 201, 202]:
            raise Exception(f"Creatomate Error {res_c.status_code}: {res_c.text}")

        render_data = res_c.json()
        render_id = render_data[0]['id']
        video_url = render_data[0]['url']

        # 5. Espera Activa
        print(f"⏳ Procesando video...")
        for _ in range(15):
            time.sleep(15)
            check = requests.get(f"https://api.creatomate.com/v2/renders/{render_id}", headers=h_c).json()
            if check.get('status') == 'succeeded':
                print("✅ Video terminado.")
                break

        # 6. Registro y Telegram
        l_amz = f"https://www.amazon.com/s?k={prod_nombre.replace(' ', '+')}&tag={AMAZON_TAG}"
        sheet.append_row([prod_nombre, l_amz, video_url])
        
        msg = f"🎬 *¡Video Listo!*\n\n📦 *Producto:* {prod_nombre}\n🎥 [Ver Video]({video_url})\n🔗 [Link Amazon]({l_amz})"
        enviar_telegram(msg)
        print("🚀 PROCESO COMPLETADO")

    except Exception as e:
        error_msg = f"❌ *Error en el Bot:* {str(e)[:200]}"
        enviar_telegram(error_msg)
        print(f"❌ Error: {e}")
        sys.exit(1)
