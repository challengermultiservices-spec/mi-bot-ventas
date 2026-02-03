import os, requests, json, gspread, time, random, sys
from google.oauth2.service_account import Credentials

def ejecutar_sistema_automatico():
    gemini_key = os.environ.get("GEMINI_API_KEY")
    creatomate_key = os.environ.get("CREATOMATE_API_KEY")
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    categorias = ["Hogar Inteligente", "Gadgets Tech", "Cocina", "Mascotas"]
    cat = random.choice(categorias)

    # Nombres exactos para la API v1 (Producción)
    intentos_api = [
        ("v1", "gemini-1.5-flash-latest"),
        ("v1", "gemini-1.5-pro-latest"),
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
            print(f"--- Solicitando a {model_name} ({api_ver}) ---")
            url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model_name}:generateContent?key={gemini_key}"
            
            payload = {
                "contents": [{"parts": [{"text": f"Producto viral Amazon {cat}. Responde SOLO: NOMBRE | BUSQUEDA | HOOK | SCRIPT"}]}],
                "generationConfig": {"temperature": 0.7}
            }
            
            r = requests.post(url, json=payload)
            res_json = r.json()
            
            if 'candidates' in res_json:
                res_g = res_json
                print(f"✅ ¡Éxito con {model_name}!")
                break
            elif 'error' in res_json:
                codigo = res_json['error']['code']
                msg = res_json['error']['message']
                print(f"⚠️ Intento fallido ({codigo}): {msg}")
                if codigo == 429:
                    print("🚀 Cuota excedida. Esperando 45 segundos para limpiar el túnel...")
                    time.sleep(45)
                else:
                    time.sleep(5)

        if not res_g:
            print("❌ No se pudo obtener respuesta de Gemini tras todos los reintentos.")
            sys.exit(1)

        # Procesamiento de la respuesta
        texto_raw = res_g['candidates'][0]['content']['parts'][0]['text']
        lineas = texto_raw.replace('```', '').replace('markdown', '').strip().split('\n')
        datos = []
        for l in lineas:
            if '|' in l:
                datos = [x.strip() for x in l.split('|')]
                break
        
        if len(datos) < 4:
            print(f"❌ Error de formato en respuesta: {texto_raw}")
            sys.exit(1)

        # Renderizado en Creatomate
        print(f"--- Renderizando Video: {datos[0]} ---")
        api_url = "[https://api.creatomate.com/v2/renders](https://api.creatomate.com/v2/renders)"
        headers = {"Authorization": f"Bearer {creatomate_key}", "Content-Type": "application/json"}
        payload_v = {
            "template_id": TEMPLATE_ID,
            "modifications": {"Text-1.text": datos[2].upper(), "Text-2.text": datos[3]}
        }
        
        res_v = requests.post(api_url, headers=headers, json=payload_v)
        video_url = res_v.json()[0]['url']

        # Guardado final
        link = f"[https://www.amazon.com/s?k=](https://www.amazon.com/s?k=){datos[1].replace(' ', '+')}&tag={AMAZON_TAG}"
        sheet.append_row([datos[0], link, video_url])
        print(f"🚀 ¡LOGRADO! Fila añadida correctamente.")

    except Exception as e:
        print(f"❌ Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
