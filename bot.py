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
        "from": {"email": receptor}, # Usamos tu propio correo verificado como remitente
        "subject": f"🚀 Video de Amazon Listo: {producto}",
        "content": [{"type": "text/plain", "value": f"Hola!\n\nEl bot ha generado un nuevo video.\nProducto: {producto}\nVer Video: {link_video}\n\nYa puedes descargarlo y subirlo."}]
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        requests.post(url, json=data, headers=headers, timeout=10)
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
    payload = {
        "To": mi_cel, 
        "From": n_twilio, 
        "Body": f"Bot Amazon: Video listo para {producto}. Revisa tu Sheets!"
    }
    try:
        requests.post(url, data=payload, auth=(sid, token), timeout=10)
        print("📱 SMS enviado con éxito.")
    except:
        print("⚠️ No se pudo enviar el SMS.")

def ejecutar_sistema_automatico():
    # Carga de Variables
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    creatomate_key = os.environ.get("CREATOMATE_API_KEY", "").strip()
    pexels_key = os.environ.get("PEXELS_API_KEY", "").strip()
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS", "").strip()
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    try:
        # 1. Google Sheets
        creds_dict = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_dict, 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        sheet = gspread.authorize(creds).open_by_key(ID_HOJA).get_worksheet(0)
        print("✅ Sheets Conectado")

        # 2. Gemini
        url_g = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        cat = random.choice(["Gadgets Tecnológicos", "Cocina Pro", "Hogar Inteligente", "Mascotas"])
        prompt = (f"Product Amazon {cat}. Return ONLY JSON object: "
                  "{\"producto\": \"Nombre Real\", \"query_v\": \"2 words english\", \"hook\": \"...\", \"script\": \"...\"}")
        
        r_g = requests.post(url_g, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        datos = json.loads(re.search(r'\{.*\}', r_g.text, re.DOTALL).group(0))
        prod_nombre = datos.get('producto', 'Nuevo Gadget')
        print(f"✅ Producto: {prod_nombre}")

        # 3. Pexels
        video_f = "https://creatomate.com/files/assets/7347c3b7-e1a8-4439-96f1-f3dfc95c3d28"
        try:
            p_res = requests.get(f"https://api.pexels.com/videos/search?query={datos['query_v']}&per_page=1&orientation=portrait", 
                                 headers={"Authorization": pexels_key}, timeout=15)
            if p_res.status_code == 200 and p_res.json().get('videos'):
                video_f = p_res.json()['videos'][0]['video_files'][0]['link']
                print("🎬 Fondo de Pexels listo.")
        except: print("⚠️ Usando fondo predeterminado.")

        # 4. Creatomate
        u_c = "https://api.creatomate.com/v2/renders"
        h_c = {"Authorization": f"Bearer {creatomate_key}", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        p_c = {
            "template_id": TEMPLATE_ID,
            "modifications": {
                "Video.source": video_f,
                "Text-1.text": datos.get('hook', 'AMAZON FIND').upper()[:60],
                "Text-2.text": datos.get('script', '')[:250]
            }
        }
        
        video_url = "Procesando..."
        try:
            res_c = requests.post(u_c, headers=h_c, json=p_c, timeout=25)
            if res_c.status_code in [200, 201, 202]:
                video_url = res_c.json()[0]['url']
        except: print("⚠️ El render se completará en breve.")

        # 5. Guardado y Alertas
        link_amz = f"https://www.amazon.com/s?k={prod_nombre.replace(' ', '+')}&tag={AMAZON_TAG}"
        sheet.append_row([prod_nombre, link_amz, video_url])
        
        print(f"🚀 EXITO TOTAL. Lanzando notificaciones...")
        enviar_email(prod_nombre, video_url)
        enviar_sms(prod_nombre)

    except Exception as e:
        print(f"❌ Error Crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
