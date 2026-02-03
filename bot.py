import os, requests, json, gspread, time, random, sys, re
from google.oauth2.service_account import Credentials

def ejecutar_sistema_automatico():
    gemini_key = os.environ.get("GEMINI_API_KEY")
    creatomate_key = os.environ.get("CREATOMATE_API_KEY")
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    cat = random.choice(["Gadgets", "Hogar", "Cocina", "Mascotas", "Fitness"])

    try:
        # 1. Conexión a Sheets
        creds_info = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_info, 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        sheet = gspread.authorize(creds).open_by_key(ID_HOJA).get_worksheet(0)
        print("✅ Base de Datos Conectada")

        # 2. Generación de Contenido (JSON Forzado)
        url_g = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        prompt = (f"Producto viral Amazon {cat}. Responde SOLO un JSON: "
                  "{\"producto\": \"...\", \"busqueda\": \"...\", \"hook\": \"...\", \"script\": \"...\"}")
        
        r = requests.post(url_g, json={"contents": [{"parts": [{"text": prompt}]}]})
        datos = json.loads(re.search(r'\{.*\}', r.json()['candidates'][0]['content']['parts'][0]['text'], re.DOTALL).group(0))
        print(f"✅ IA generó: {datos['producto']}")

        # 3. Producción de Video con Reintento ante Error 0
        print(f"--- Iniciando Producción en Creatomate ---")
        u_c = "https://api.creatomate.com/v2/renders"
        h_c = {"Authorization": f"Bearer {creatomate_key}", "Content-Type": "application/json"}
        payload_v = {
            "template_id": TEMPLATE_ID,
            "modifications": {
                "Text-1.text": datos['hook'].upper()[:60],
                "Text-2.text": datos['script'][:300]
            }
        }
        
        res_data = None
        for intento in range(3):
            try:
                res_v = requests.post(u_c, headers=h_c, json=payload_v)
                if res_v.status_code in [200, 201, 202]:
                    res_data = res_v.json()[0]
                    break
            except Exception:
                print(f"⚠️ Reintentando conexión con Creatomate... ({intento+1}/3)")
                time.sleep(5)

        if not res_data:
            print("❌ Creatomate no respondió tras 3 intentos.")
            sys.exit(1)

        # 4. Verificación de URL y Pausa de Renderizado
        video_url = res_data.get('url')
        print(f"⏳ Procesando video: {video_url}")
        time.sleep(10) # Pausa de seguridad para que el archivo se asiente

        # 5. Guardado Final
        link = f"https://www.amazon.com/s?k={datos['busqueda'].replace(' ', '+')}&tag={AMAZON_TAG}"
        sheet.append_row([datos['producto'], link, video_url])
        print(f"🚀 ¡FINALIZADO! Revisa tu Excel.")

    except Exception as e:
        print(f"❌ Error final: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
