import os, requests, json, gspread, time, random, sys, re
from google.oauth2.service_account import Credentials

def ejecutar_sistema_automatico():
    # Limpiamos las llaves de posibles espacios invisibles
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    creatomate_key = os.environ.get("CREATOMATE_API_KEY", "").strip()
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS", "").strip()
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    cat = random.choice(["Mascotas", "Cocina", "Gadgets", "Hogar"])

    try:
        # 1. Conexión a Sheets
        creds_info = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_info, 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        sheet = gspread.authorize(creds).open_by_key(ID_HOJA).get_worksheet(0)
        print("✅ Conectado a Sheets")

        # 2. Gemini 2.5 Flash
        url_g = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        prompt = f"Producto Amazon viral {cat}. Responde SOLO un JSON: {{\"producto\": \"...\", \"busqueda\": \"...\", \"hook\": \"...\", \"script\": \"...\"}}"
        
        r = requests.post(url_g, json={"contents": [{"parts": [{"text": prompt}]}]})
        res_json = r.json()
        
        # Extraer JSON de la respuesta de la IA
        raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
        datos = json.loads(re.search(r'\{.*\}', raw_text, re.DOTALL).group(0))
        print(f"✅ Producto: {datos['producto']}")

        # 3. Llamada a Creatomate (Simplificada y con Logs)
        print("--- Intentando conexión con Creatomate ---")
        u_c = "https://api.creatomate.com/v2/renders"
        
        payload_v = {
            "template_id": TEMPLATE_ID,
            "modifications": {
                "Text-1.text": datos['hook'].upper()[:50],
                "Text-2.text": datos['script'][:280]
            }
        }
        
        headers = {
            "Authorization": f"Bearer {creatomate_key}",
            "Content-Type": "application/json"
        }

        # Realizamos la petición sin bucles complejos para ver el error real
        res_v = requests.post(u_c, headers=headers, json=payload_v, timeout=30)
        
        if res_v.status_code not in [200, 201, 202]:
            print(f"❌ Error de Creatomate (Status {res_v.status_code}): {res_v.text}")
            sys.exit(1)

        video_url = res_v.json()[0]['url']
        print(f"⏳ Video solicitado: {video_url}")

        # 4. Guardado Final
        link = f"https://www.amazon.com/s?k={datos['busqueda'].replace(' ', '+')}&tag={AMAZON_TAG}"
        sheet.append_row([datos['producto'], link, video_url])
        print(f"🚀 ¡CONSEGUIDO! Fila guardada.")

    except Exception as e:
        print(f"❌ Error Crítico: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
