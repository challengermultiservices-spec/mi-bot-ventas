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

    # USAMOS LOS NOMBRES QUE EL DEBUG CONFIRMÓ
    intentos_api = [
        ("v1beta", "gemini-2.5-flash"), 
        ("v1beta", "gemini-2.0-flash"),
        ("v1beta", "gemini-1.5-flash-latest")
    ]

    try:
        # 1. Conexión a Sheets
        print("--- Conectando a Google Sheets ---")
        creds_info = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_info, 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        client = gspread.authorize(creds)
        sheet = client.open_by_key(ID_HOJA).get_worksheet(0)
        print("✅ Conexión con Sheets exitosa.")

        # 2. Gemini
        res_g = None
        for api_ver, model_name in intentos_api:
            print(f"--- Solicitando a {model_name}... ---")
            url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model_name}:generateContent?key={gemini_key}"
            payload = {"contents": [{"parts": [{"text": f"Producto viral Amazon {cat}. Responde SOLO: NOMBRE | BUSQUEDA | HOOK | SCRIPT"}]}]}
            
            try:
                r = requests.post(url, json=payload, timeout=30)
                res_json = r.json()
                if 'candidates' in res_json:
                    res_g = res_json
                    print(f"✅ ¡Éxito con {model_name}!")
                    break
                else:
                    print(f"⚠️ {model_name} no respondió: {res_json.get('error', {}).get('message', 'Error de cuota o región')}")
            except Exception as e:
                print(f"⚠️ Error de red: {e}")
            
            time.sleep(5) # Pausa de cortesía para la API

        if not res_g:
            print("❌ No se pudo conectar con los nuevos modelos. Verifica tu facturación.")
            sys.exit(1)

        # 3. Procesamiento
        texto = res_g['candidates'][0]['content']['parts'][0]['text']
        datos = [x.strip() for x in texto.replace('```', '').replace('markdown', '').split('|') if x.strip()]
        
        if len(datos) < 4:
            # Fallback por si responde en líneas
            datos = [x.strip() for x in texto.split('\n') if x.strip()][:4]

        # 4. Creatomate
        print(f"--- Renderizando Video: {datos[0]} ---")
        api_url = "[https://api.creatomate.com/v2/renders](https://api.creatomate.com/v2/renders)"
        headers = {"Authorization": f"Bearer {creatomate_key}", "Content-Type": "application/json"}
        payload_v = {
            "template_id": TEMPLATE_ID,
            "modifications": {
                "Text-1.text": datos[2].upper(),
                "Text-2.text": datos[3]
            }
        }
        res_v = requests.post(api_url, headers=headers, json=payload_v)
        video_url = res_v.json()[0]['url']
        
        # 5. Guardado Final
        link = f"[https://www.amazon.com/s?k=](https://www.amazon.com/s?k=){datos[1].replace(' ', '+')}&tag={AMAZON_TAG}"
        sheet.append_row([datos[0], link, video_url])
        print(f"🚀 ¡LOGRADO! Fila añadida para {datos[0]}")

    except Exception as e:
        print(f"❌ Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
