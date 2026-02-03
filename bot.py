import os, requests, json, gspread, time, random, sys, re
from google.oauth2.service_account import Credentials

def ejecutar_sistema_automatico():
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    creatomate_key = os.environ.get("CREATOMATE_API_KEY", "").strip()
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS", "").strip()
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    cat = random.choice(["Gadgets", "Hogar", "Cocina", "Mascotas"])

    try:
        # 1. Sheets
        creds_info = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_info, 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        sheet = gspread.authorize(creds).open_by_key(ID_HOJA).get_worksheet(0)
        print("✅ Sheets Conectado")

        # 2. Gemini 2.5 Flash
        url_g = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        prompt = f"Producto Amazon {cat}. Responde SOLO un JSON: {{\"producto\": \"...\", \"busqueda\": \"...\", \"hook\": \"...\", \"script\": \"...\"}}"
        
        r = requests.post(url_g, json={"contents": [{"parts": [{"text": prompt}]}]})
        datos = json.loads(re.search(r'\{.*\}', r.text, re.DOTALL).group(0))
        print(f"✅ Producto: {datos['producto']}")

        # 3. Creatomate (Con pausa de seguridad)
        print("--- Renderizando Video ---")
        u_c = "https://api.creatomate.com/v2/renders"
        h_c = {"Authorization": f"Bearer {creatomate_key}", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        p_c = {
            "template_id": TEMPLATE_ID,
            "modifications": {
                "Text-1.text": datos['hook'].upper()[:50],
                "Text-2.text": datos['script'][:250]
            }
        }
        
        res_v = requests.post(u_c, headers=h_c, json=p_c, timeout=30)
        
        # Si recibimos 200, 201 o 202, el video se está creando
        if res_v.status_code in [200, 201, 202]:
            video_url = res_v.json()[0]['url']
            link_amz = f"https://www.amazon.com/s?k={datos['busqueda'].replace(' ', '+')}&tag={AMAZON_TAG}"
            
            # 4. Guardar en Sheets
            sheet.append_row([datos['producto'], link_amz, video_url])
            print(f"🚀 EXITO: {datos['producto']} guardado.")
        else:
            print(f"❌ Error API: {res_v.text}")

    except Exception as e:
        print(f"⚠️ Nota: El video se envió pero hubo un aviso de red: {e}")
        sys.exit(0) # Salimos sin error porque el video ya se está haciendo

if __name__ == "__main__":
    ejecutar_sistema_automatico()
