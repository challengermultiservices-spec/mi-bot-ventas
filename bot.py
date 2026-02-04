import os, requests, json, gspread, time, random, sys, re
from google.oauth2.service_account import Credentials

def enviar_telegram(mensaje):
    token = os.environ.get("TELEGRAM_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": mensaje, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def ejecutar_bot():
    # 1. Carga de Variables
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    creatomate_key = os.environ.get("CREATOMATE_API_KEY", "").strip()
    pexels_key = os.environ.get("PEXELS_API_KEY", "").strip()
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS", "").strip()
    
    # IDs de tus herramientas
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"
    AMAZON_TAG = "chmbrand-20"

    print("🚀 Iniciando Bot...")

    try:
        # 2. Conexión Google Sheets
        creds_dict = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_dict, 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        sheet = gspread.authorize(creds).open_by_key(ID_HOJA).get_worksheet(0)
        print("✅ Sheets Conectado")

        # 3. Gemini: Generar Producto
        url_g = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
        prompt = "Suggest 1 viral Amazon gadget. Return ONLY JSON: {\"prod\": \"Name\", \"query\": \"English Search\", \"hook\": \"Short Hook\", \"body\": \"Short Body\"}"
        r_g = requests.post(url_g, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        datos = json.loads(re.search(r'\{.*\}', r_g.text, re.DOTALL).group(0))
        prod_nombre = datos.get('prod', 'Gadget Viral')
        print(f"✅ Producto: {prod_nombre}")

        # 4. Pexels: Fondo de Video
        video_f = "https://creatomate.com/files/assets/7347c3b7-e1a8-4439-96f1-f3dfc95c3d28"
        try:
            h_p = {"Authorization": pexels_key}
            p_res = requests.get(f"https://api.pexels.com/videos/search?query={datos['query']}&per_page=1&orientation=portrait", headers=h_p, timeout=20)
            if p_res.status_code == 200:
                video_f = p_res.json()['videos'][0]['video_files'][0]['link']
                print("🎬 Fondo de Pexels obtenido")
        except:
            print("⚠️ Usando fondo por defecto")

        # 5. Creatomate: Renderizado
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
        res_c = requests.post(u_c, headers=h_c, json=payload, timeout=45).json()
        render_id = res_c[0]['id']
        video_url = res_c[0]['url']

        # 6. Espera Activa (Máximo 3 mins)
        print("⏳ Procesando video...")
        for _ in range(12):
            time.sleep(15)
            check = requests.get(f"https://api.creatomate.com/v2/renders/{render_id}", headers=h_c).json()
            if check.get('status') == 'succeeded':
                print("✅ Video terminado")
                break

        # 7. Registro y Notificación
        l_amz = f"https://www.amazon.com/s?k={prod_nombre.replace(' ', '+')}&tag={AMAZON_TAG}"
        sheet.append_row([prod_nombre, l_amz, video_url])
        
        msg = f"🎬 *¡Video Listo!*\n\n📦 *Producto:* {prod_nombre}\n🎥 [Ver Video]({video_url})\n🛒 [Link Amazon]({l_amz})"
        enviar_telegram(msg)
        print("🏁 PROCESO COMPLETADO")

    except Exception as e:
        error_info = f"❌ *Error en el Bot:* {str(e)}"
        enviar_telegram(error_info)
        print(error_info)
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_bot()
