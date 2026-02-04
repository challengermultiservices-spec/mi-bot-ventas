import os, requests, json, gspread, time, random, sys, re
from google.oauth2.service_account import Credentials

# --- NOTIFICACIÓN POR EMAIL (SENDGRID) CON DIAGNÓSTICO ---
def enviar_email(producto, link_video):
    api_key = os.environ.get("SENDGRID_API_KEY", "").strip()
    receptor = os.environ.get("EMAIL_RECEPTOR", "").strip()
    if not api_key or not receptor: 
        print("⚠️ Error: Faltan SENDGRID_API_KEY o EMAIL_RECEPTOR en Secrets.")
        return

    url = "https://api.sendgrid.com/v3/mail/send"
    data = {
        "personalizations": [{"to": [{"email": receptor}]}],
        "from": {"email": receptor}, 
        "subject": f"🎬 Video de Amazon Listo: {producto}",
        "content": [{"type": "text/plain", "value": f"¡Hola!\n\nEl video para '{producto}' está listo.\nVer Video: {link_video}"}]
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    try:
        res = requests.post(url, json=data, headers=headers, timeout=15)
        if res.status_code in [200, 201, 202]:
            print("📧 Email enviado con éxito.")
        else:
            print(f"❌ Error SendGrid (Código {res.status_code}): {res.text}")
    except Exception as e:
        print(f"⚠️ Fallo crítico en el envío de Email: {e}")

# --- NOTIFICACIÓN POR SMS (TWILIO) CON DIAGNÓSTICO ---
def enviar_sms(producto):
    sid = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
    token = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
    n_twilio = os.environ.get("TWILIO_PHONE", "").strip()
    mi_cel = os.environ.get("MI_CELULAR", "").strip()
    
    if not all([sid, token, n_twilio, mi_cel]):
        print("⚠️ Error: Faltan credenciales de Twilio en Secrets.")
        return

    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    payload = {"To": mi_cel, "From": n_twilio, "Body": f"Bot Amazon: ¡Video listo para {producto}!"}
    
    try:
        res = requests.post(url, data=payload, auth=(sid, token), timeout=15)
        if res.status_code in [200, 201]:
            print("📱 SMS enviado con éxito.")
        else:
            print(f"❌ Error Twilio (Código {res.status_code}): {res.text}")
    except Exception as e:
        print(f"⚠️ Fallo crítico en el envío de SMS: {e}")

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
        prompt = "Product Amazon Gadgets. Return ONLY JSON: {\"prod\": \"...\", \"query\": \"...\", \"hook\": \"...\", \"body\": \"...\"}"
        r_g = requests.post(url_g, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        datos = json.loads(re.search(r'\{.*\}', r_g.text, re.DOTALL).group(0))
        prod_nombre = datos.get('prod', 'Nuevo Gadget')
        print(f"✅ Producto: {prod_nombre}")

        # 3. Pexels (Fondo)
        video_f = "https://creatomate.com/files/assets/7347c3b7-e1a8-4439-96f1-f3dfc95c3d28"
        try:
            p_res = requests.get(f"https://api.pexels.com/videos/search?query={datos['query']}&per_page=1&orientation=portrait", 
                                 headers={"Authorization": pexels_key}, timeout=20)
            if p_res.status_code == 200 and p_res.json().get('videos'):
                video_f = p_res.json()['videos'][0]['video_files'][0]['link']
        except: pass

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
        video_url = "https://creatomate.com/renders"
        try:
            res_c = requests.post(u_c, headers=h_c, json=payload, timeout=45).json()
            video_url = res_c[0]['url']
        except: 
            print("⚠️ Aviso de red en Creatomate.")

        # 5. Guardado y Notificación
        l_amz = f"https://www.amazon.com/s?k={prod_nombre.replace(' ', '+')}&tag={AMAZON_TAG}"
        sheet.append_row([prod_nombre, l_amz, video_url])
        
        print(f"🚀 PROCESO FINALIZADO. Lanzando diagnósticos...")
        enviar_email(prod_nombre, video_url)
        enviar_sms(prod_nombre)

    except Exception as e:
        print(f"❌ Error Real Detectado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_bot_maestro()
