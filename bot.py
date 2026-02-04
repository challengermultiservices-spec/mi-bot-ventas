import os, requests, json, gspread, time, random, sys, re
from google.oauth2.service_account import Credentials

# --- NOTIFICACIÓN POR EMAIL (SENDGRID) ---
def enviar_email(producto, link_video):
    api_key = os.environ.get("SENDGRID_API_KEY", "").strip()
    receptor = os.environ.get("EMAIL_RECEPTOR", "").strip()
    if not api_key or not receptor: return
    url = "https://api.sendgrid.com/v3/mail/send"
    data = {
        "personalizations": [{"to": [{"email": receptor}]}],
        "from": {"email": receptor}, 
        "subject": f"🎬 Video de Amazon Listo: {producto}",
        "content": [{"type": "text/plain", "value": f"¡Hola!\n\nEl video para '{producto}' ya está listo.\n\nVer Video: {link_video}"}]
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        requests.post(url, json=data, headers=headers, timeout=15)
        print("📧 Email enviado con éxito.")
    except:
        print("⚠️ No se pudo enviar el Email.")

# --- NOTIFICACIÓN POR SMS (TWILIO) ---
def enviar_sms(producto):
    sid = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
    token = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
    n_twilio = os.environ.get("TWILIO_PHONE", "").strip()
    mi_cel = os.environ.get("MI_CELULAR", "").strip()
    if not all([sid, token, n_twilio, mi_cel]): return
    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    payload = {"To": mi_cel, "From": n_twilio, "Body": f"Bot Amazon: ¡Video listo para {producto}!"}
    try:
        requests.post(url, data=payload, auth=(sid, token), timeout=15)
        print("📱 SMS enviado con éxito.")
    except:
        print("⚠️ No se pudo enviar el SMS.")

def ejecutar_bot_maestro():
    # Carga de Secretos
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    creatomate_key = os.environ.get("CREATOMATE_API_KEY", "").strip()
    pexels_key = os.environ.get("PEXELS_API_KEY", "").strip()
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS", "").strip()
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    try:
        # 1. Conexión Sheets
        creds_dict = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_dict, 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        sheet = gspread.authorize(creds).open_by_key(ID_HOJA).get_worksheet(0)
        print("✅ Sheets Conectado")

        # 2. Gemini
        url_g = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
        cat = random.choice(["Gadgets", "Cocina", "Hogar", "Mascotas"])
        prompt = f"Product Amazon {cat}. Return ONLY JSON: {{\"prod\": \"...\", \"query\": \"...\", \"hook\": \"...\", \"body\": \"...\"}}"
        
        r_g = requests.post(url_g, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        datos = json.loads(re.search(r'\{.*\}', r_g.text, re.DOTALL).group(0))
        prod_nombre = datos.get('prod', 'Nuevo Gadget')
        print(f"✅ Producto: {prod_nombre}")

        # 3. Pexels
        video_f = "https://creatomate.com/files/assets/7347c3b7-e1a8-4439-96f1-f3dfc95c3d28"
        try:
            p_res = requests.get(f"https://api.pexels.com/videos/search?query={datos['query']}&per_page=1&orientation=portrait", 
                                 headers={"Authorization": pexels_key}, timeout=20)
            if p_res.status_code == 200 and p_res.json().get('videos'):
                video_f = p_res.json()['videos'][0]['video_files'][0]['link']
                print("🎬 Fondo de Pexels listo.")
        except: print("⚠️ Usando fondo por defecto.")

       # 4. Creatomate
        u_c = "https://api.creatomate.com/v2/renders"
        h_c = {"Authorization": f"Bearer {creatomate_key}", "Content-Type": "application/json"}
        payload = {
            "template_id": TEMPLATE_ID,
            "modifications": {
                "Video.source": video_f,
                "Text-1.text": datos.get('hook', 'OFERTA').upper()[:60],
                "Text-2.text": datos.get('body', '')[:250]
            }
        }
        
        print("🚀 Enviando orden a Creatomate...")
        res_c = requests.post(u_c, headers=h_c, json=payload, timeout=45).json()
        render_id = res_c[0]['id']
        video_url = res_c[0]['url']

        # Bucle de espera
        print(f"⏳ Procesando video...")
        for _ in range(16):
            time.sleep(15)
            check = requests.get(f"https://api.creatomate.com/v2/renders/{render_id}", headers=h_c, timeout=20).json()
            if check.get('status') == 'succeeded':
                print("✅ Video terminado.")
                break
            print("... trabajando ...")

        # 5. Guardado y Notificación
        l_amz = f"https://www.amazon.com/s?k={prod_nombre.replace(' ', '+')}&tag={AMAZON_TAG}"
        sheet.append_row([prod_nombre, l_amz, video_url])
        
        print(f"🚀 TODO LISTO. Notificando...")
        enviar_email(prod_nombre, video_url)
        enviar_sms(prod_nombre)

    except Exception as e:
        print(f"❌ Error Crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_bot_maestro()
