import os
import requests
import json
import gspread
from google.oauth2.service_account import Credentials
import sys

def ejecutar_sistema_automatico():
    gemini_key = os.environ.get("GEMINI_API_KEY")
    creatomate_key = os.environ.get("CREATOMATE_API_KEY")
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    try:
        # 1. Conexión a Sheets
        print("--- Conectando a Google Sheets ---")
        creds_json = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_json, scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        client = gspread.authorize(creds)
        sheet = client.open_by_key(ID_HOJA).get_worksheet(0)

        # 2. Diagnóstico de Modelos (Para ver qué tienes activo)
        print("--- Verificando modelos disponibles en tu cuenta ---")
        url_list = f"https://generativelanguage.googleapis.com/v1beta/models?key={gemini_key}"
        res_list = requests.get(url_list).json()
        
        if 'models' in res_list:
            modelos_nombres = [m['name'] for m in res_list['models']]
            print(f"Modelos detectados: {modelos_nombres[:5]}...") # Muestra los primeros 5
        else:
            print(f"⚠️ No se pudieron listar modelos: {res_list}")

        # 3. Intento con el nombre más actual y estable
        print("--- Pidiendo producto a Gemini (flash-latest) ---")
        url_gemini = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={gemini_key}"
        
        payload_gemini = {
            "contents": [{"parts": [{"text": "Dame un producto viral de Amazon. Formato: NOMBRE | BUSQUEDA | HOOK | SCRIPT"}]}]
        }
        
        response = requests.post(url_gemini, json=payload_gemini)
        res_g = response.json()

        if 'candidates' not in res_g:
            print(f"❌ Error crítico: Tu API Key no encuentra el modelo. Respuesta: {json.dumps(res_g)}")
            print("💡 TIP: Ve a https://aistudio.google.com/ y asegúrate de crear una API KEY nueva.")
            sys.exit(1)

        # 4. Procesamiento de datos
        texto_respuesta = res_g['candidates'][0]['content']['parts'][0]['text']
        datos = [d.strip() for d in texto_respuesta.split('|')]
        producto, busqueda, hook, cuerpo = datos[0], datos[1], datos[2], datos[3]

        # 5. Amazon Link y Creatomate
        link_afiliado = f"https://www.amazon.com/s?k={busqueda.replace(' ', '+')}&tag={AMAZON_TAG}"
        
        print(f"--- Enviando a Creatomate: {producto} ---")
        headers_c = {"Authorization": f"Bearer {creatomate_key}", "Content-Type": "application/json"}
        payload_c = {
            "template_id": TEMPLATE_ID,
            "modifications": {
                "Text-1.text": hook.upper(),
                "Text-2.text": cuerpo
            }
        }
        
        res_c = requests.post("https://api.creatomate.com/v2/renders", headers=headers_c, json=payload_c)
        video_final_url = res_c.json()[0]['url']

        # 6. Guardar en Sheets (Columna U es la 21)
        fila = [""] * 21 
        fila[0] = producto
        fila[1] = link_afiliado
        fila[2] = video_final_url
        fila[20] = "AUTO-2026"

        sheet.append_row(fila)
        print(f"✅ EXITO: Guardado en Sheets.")

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
