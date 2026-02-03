import os, requests, json, gspread, time, random, sys, re
from google.oauth2.service_account import Credentials

def ejecutar_sistema_automatico():
    # --- CONFIGURACIÓN ---
    gemini_key = os.environ.get("GEMINI_API_KEY")
    creatomate_key = os.environ.get("CREATOMATE_API_KEY")
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    # Categorías para variedad infinita
    cat = random.choice(["Gadgets Tecnológicos", "Hogar Inteligente", "Cocina Pro", "Mascotas VIP", "Fitness", "Gaming"])

    try:
        # 1. Conexión a Sheets
        creds_info = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_info, 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        sheet = gspread.authorize(creds).open_by_key(ID_HOJA).get_worksheet(0)
        print("✅ Conectado a la Base de Datos")

        # 2. Gemini 2.5 Flash - FORMATO JSON FORZADO (Inmune a errores de lectura)
        url_g = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        
        prompt = (f"Actúa como un experto en marketing de Amazon. Sugiere un producto viral de {cat}. "
                  "Responde EXCLUSIVAMENTE con un objeto JSON válido con estas llaves: "
                  "\"producto\", \"busqueda\", \"hook\", \"script\". "
                  "En 'script' pon solo la narración, sin instrucciones visuales, máximo 300 caracteres.")
        
        r = requests.post(url_g, json={"contents": [{"parts": [{"text": prompt}]}]})
        res_text = r.json()['candidates'][0]['content']['parts'][0]['text']
        
        # Extraer JSON del texto (por si la IA pone texto extra)
        match = re.search(r'\{.*\}', res_text, re.DOTALL)
        if not match:
            print(f"❌ La IA no envió JSON. Recibido: {res_text}")
            sys.exit(1)
            
        datos = json.loads(match.group(0))
        print(f"✅ Producto Generado: {datos['producto']}")

        # 3. Preparación de Datos
        # Acortamos el texto para evitar el Error 0 de Creatomate por exceso de caracteres
        hook_final = datos['hook'].upper()[:60]
        script_final = datos['script'][:400]
        link = f"https://www.amazon.com/s?k={datos['busqueda'].replace(' ', '+')}&tag={AMAZON_TAG}"

        # 4. Creatomate - Renderizado Robusto
        print(f"--- Iniciando Producción de Video ---")
        u_c = "https://api.creatomate.com/v2/renders"
        h_c = {"Authorization": f"Bearer {creatomate_key}", "Content-Type": "application/json"}
        
        payload_v = {
            "template_id": TEMPLATE_ID,
            "modifications": {
                "Text-1.text": hook_final,
                "Text-2.text": script_final
            }
        }
        
        res_v = requests.post(u_c, headers=h_c, json=payload_v)
        res_data = res_v.json()
        
        if res_v.status_code != 200:
            print(f"❌ Error en Creatomate (Status {res_v.status_code}): {res_v.text}")
            sys.exit(1)
            
        video_url = res_data[0]['url']

        # 5. Guardado Final
        sheet.append_row([datos['producto'], link, video_url])
        print(f"🚀 ¡MISIÓN CUMPLIDA! Video en cola: {datos['producto']}")

    except Exception as e:
        print(f"❌ Error Crítico del Sistema: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
