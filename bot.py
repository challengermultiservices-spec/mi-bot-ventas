import os, requests, json, gspread, time, random, sys, re
from google.oauth2.service_account import Credentials

def ejecutar_sistema_automatico():
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    creatomate_key = os.environ.get("CREATOMATE_API_KEY", "").strip()
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS", "").strip()
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    try:
        # 1. Google Sheets
        creds_info = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_info, 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        sheet = gspread.authorize(creds).open_by_key(ID_HOJA).get_worksheet(0)
        print("✅ Sheets Conectado")

        # 2. Gemini - Generación con Reintento
        url_g = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        cat = random.choice(["Gadgets", "Cocina", "Hogar", "Mascotas"])
        prompt = f"Producto Amazon viral {cat}. Responde SOLO un JSON: {{\"producto\": \"...\", \"busqueda\": \"...\", \"hook\": \"...\", \"script\": \"...\"}}"
        
        r = requests.post(url_g, json={"contents": [{"parts": [{"text": prompt}]}]})
        res_json = r.json()
        
        # Extracción flexible de JSON
        raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        
        if match:
            datos = json.loads(match.group(0))
            # Aseguramos que existan las llaves aunque la IA use mayúsculas/minúsculas
            prod = datos.get('producto') or datos.get('PRODUCTO') or "Producto Viral"
            busq = datos.get('busqueda') or datos.get('BUSQUEDA') or prod
            hook = datos.get('hook') or datos.get('HOOK') or "¡Mira esto!"
            scri = datos.get('script') or datos.get('SCRIPT') or "Increíble gadget."
        else:
            raise Exception("Formato JSON no encontrado")

        print(f"✅ Procesando: {prod}")

        # 3. Creatomate
        u_c = "https://api.creatomate.com/v2/renders"
        h_c = {"Authorization": f"Bearer {creatomate_key}", "Content-Type": "application/json"}
        p_c = {
            "template_id": TEMPLATE_ID,
            "modifications": {
                "Text-1.text": hook.upper()[:60],
                "Text-2.text": scri[:300]
            }
        }
        
        res_v = requests.post(u_c, headers=h_c, json=p_c, timeout=30)
        
        if res_v.status_code in [200, 201, 202]:
            video_url = res_v.json()[0]['url']
            link_amz = f"https://www.amazon.com/s?k={busq.replace(' ', '+')}&tag={AMAZON_TAG}"
            sheet.append_row([prod, link_amz, video_url])
            print(f"🚀 EXITO: {prod} guardado.")
        else:
            print(f"❌ Error API Creatomate: {res_v.text}")

    except Exception as e:
        print(f"❌ Error en ejecución: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
