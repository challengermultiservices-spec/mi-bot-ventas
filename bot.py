import os, requests, json, gspread, time, random, sys
from google.oauth2.service_account import Credentials

def ejecutar_sistema_automatico():
    gemini_key = os.environ.get("GEMINI_API_KEY")
    creatomate_key = os.environ.get("CREATOMATE_API_KEY")
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    categorias = ["Hogar", "Gadgets", "Cocina", "Mascotas"]
    cat = random.choice(categorias)

    # Nombres BASE oficiales. Estos son los más compatibles.
    intentos_api = [
        ("v1beta", "gemini-1.5-flash"),
        ("v1beta", "gemini-1.5-pro"),
        ("v1beta", "gemini-2.0-flash-exp")
    ]

    try:
        print("--- Conectando a Google Sheets ---")
        creds_info = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_info, 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        client = gspread.authorize(creds)
        sheet = client.open_by_key(ID_HOJA).get_worksheet(0)
        print("✅ Conexión con Sheets exitosa.")

        res_g = None
        for api_ver, model_name in intentos_api:
            print(f"--- Intentando con {model_name} en {api_ver} ---")
            url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model_name}:generateContent?key={gemini_key}"
            
            payload = {
                "contents": [{"parts": [{"text": f"Producto viral Amazon {cat}. Responde SOLO: NOMBRE | BUSQUEDA | HOOK | SCRIPT"}]}]
            }
            
            r = requests.post(url, json=payload)
            res_json = r.json()
            
            if 'candidates' in res_json:
                res_g = res_json
                print(f"✅ ¡Éxito con {model_name}!")
                break
            else:
                err = res_json.get('error', {})
                print(f"⚠️ Fallo {model_name}: {err.get('message', 'Sin mensaje')}")
                time.sleep(2)

        if not res_g:
            print("❌ Ningún modelo funcionó. Verificando disponibilidad de modelos para tu cuenta...")
            # Diagnóstico: Listar modelos disponibles
            diag_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={gemini_key}"
            diag_r = requests.get(diag_url).json()
            modelos_disponibles = [m['name'] for m in diag_r.get('models', [])]
            print(f"DEBUG: Modelos que tu API Key puede ver: {modelos_disponibles}")
            sys.exit(1)

        # Procesamiento
        texto = res_g['candidates'][0]['content']['parts'][0]['text']
        datos = [x.strip() for x in texto.replace('```', '').split('|') if x.strip()]
        
        if len(datos) < 4:
            # Reintento de partición si falló el pipe
            datos = [x.strip() for x in texto.split('\n') if x.strip()][:4]

        # Creatomate
        print(f"--- Renderizando Video: {datos[0]} ---")
        res_v = requests.post("[https://api.creatomate.com/v2/renders](https://api.creatomate.com/v2/renders)", 
            headers={"Authorization": f"Bearer {creatomate_key}", "Content-Type": "application/json"},
            json={"template_id": TEMPLATE_ID, "modifications": {"Text-1.text": datos[2].upper(), "Text-2.text": datos[3]}})
        
        video_url = res_v.json()[0]['url']
        link = f"[https://www.amazon.com/s?k=](https://www.amazon.com/s?k=){datos[1].replace(' ', '+')}&tag={AMAZON_TAG}"
        
        sheet.append_row
