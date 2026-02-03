import os, requests, json, gspread, time, random, sys, re
from google.oauth2.service_account import Credentials

def ejecutar_sistema_automatico():
    # Limpieza de llaves
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    creatomate_key = os.environ.get("CREATOMATE_API_KEY", "").strip()
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS", "").strip()
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    cat = random.choice(["Gadgets", "Hogar", "Cocina", "Mascotas", "Fitness"])

    try:
        # 1. Google Sheets
        creds_info = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_info, 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        sheet = gspread.authorize(creds).open_by_key(ID_HOJA).get_worksheet(0)
        print("✅ Sheets Conectado")

        # 2. Gemini 2.5 Flash (Formato JSON Estricto)
        url_g = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        prompt = (f"Producto viral Amazon {cat}. Responde SOLO un JSON con: "
                  "\"producto\", \"busqueda\", \"hook\", \"script\". "
                  "Script sin notas visuales, max 250 caracteres.")
        
        r = requests.post(url_g, json={"contents": [{"parts": [{"text": prompt}]}]})
        raw_text = r.json()['candidates'][0]['content']['parts'][0]['text']
        datos = json.loads(re.search(r'\{.*\}', raw_text, re.DOTALL).group(0))
        print(f"✅ IA generó: {datos['producto']}")

        # 3. Creatomate (Con Headers Anti-Bloqueo)
        print("--- Iniciando Creatomate ---")
        u_c = "https://api.creatomate.com/v2/renders"
        h_c = {
            "Authorization": f"Bearer {creatomate_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }
        p_c = {
            "template_id": TEMPLATE_ID,
            "modifications": {
                "Text-1.text": datos['hook'].upper()[:60],
                "Text-2.text": datos['script'][:300]
            }
        }
        
        res_v = requests.post(u_c, headers=h_c, json=p_c, timeout=60)
        
        if res_v.status_code not in [200, 201, 202]:
            print(f"❌ Error API: {res_v.text}")
            sys.exit(1)

        video_url = res_v.json()[0]['url']
        print(f"⏳ Video en proceso: {video_url}")
        time.sleep(10) # Espera para que el render arranque

        # 4. Guardado Final
        link = f"https://www.amazon.com/s?k={datos['busqueda'].replace(' ', '+')}&tag={AMAZON_TAG}"
        sheet.append_row([datos['producto'], link, video_url])
        print(f"🚀 EXITO: {datos['producto']} guardado.")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
