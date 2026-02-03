import os
import requests
import json
import gspread
from google.oauth2.service_account import Credentials
import sys

def ejecutar_sistema_automatico():
    # 1. Configuración
    gemini_key = os.environ.get("GEMINI_API_KEY")
    creatomate_key = os.environ.get("CREATOMATE_API_KEY")
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    try:
        # Conexión a Sheets
        print("--- Conectando a Google Sheets ---")
        creds_json = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_json, scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        client = gspread.authorize(creds)
        sheet = client.open_by_key(ID_HOJA).get_worksheet(0)

        # 2. Gemini: Usando gemini-pro (El más compatible)
        print("--- Pidiendo producto a Gemini (Modelo Pro) ---")
        # Usamos la versión de API v1beta con gemini-pro
        url_gemini = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={gemini_key}"
        
        payload_gemini = {
            "contents": [{"parts": [{"text": "Dame un producto de Amazon para vender. Formato: NOMBRE | BUSQUEDA | HOOK | SCRIPT"}]}]
        }
        
        response = requests.post(url_gemini, json=payload_gemini)
        res_g = response.json()

        # Si gemini-pro falla, intentamos una última vez con el nombre técnico completo
        if 'error' in res_g:
            print("--- Reintentando con nombre técnico completo ---")
            url_gemini = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.0-pro:generateContent?key={gemini_key}"
            response = requests.post(url_gemini, json=payload_gemini)
            res_g = response.json()

        if 'candidates' not in res_g:
            print(f"❌ Error Final de Gemini: {json.dumps(res_g, indent=2)}")
            sys.exit(1)

        texto_respuesta = res_g['candidates'][0]['content']['parts'][0]['text']
        datos = [d.strip() for d in texto_respuesta.split('|')]
        
        if len(datos) < 4:
            print(f"❌ Formato incorrecto: {texto_respuesta}")
            sys.exit(1)

        producto, busqueda, hook, cuerpo = datos[0], datos[1], datos[2], datos[3]

        # 3. Amazon Link y Creatomate
        link_afiliado = f"https://www.amazon.com/s?k={busqueda.replace(' ', '+')}&tag={AMAZON_TAG}"
        
        print(f"--- Enviando a Creatomate: {producto} ---")
        headers_c = {
            "Authorization": f"Bearer {creatomate_key}",
            "Content-Type": "application/json"
        }
        
        payload_c = {
            "template_id": TEMPLATE_ID,
            "modifications": {
                "Text-1.text": hook.upper(),
                "Text-2.text": cuerpo
            }
        }
        
        res_c = requests.post("https://api.creatomate.com/v2/renders", headers=headers_c, json=payload_c)
        
        if res_c.status_code not in [200, 201]:
            print(f"❌ Error Creatomate: {res_c.text}")
            sys.exit(1)

        video_final_url = res_c.json()[0]['url']

        # 4. Guardar en Sheets (Columna U es la 21)
        fila = [""] * 21 
        fila[0] = producto
        fila[1] = link_afiliado
        fila[2] = video_final_url
        fila[20] = "AUTO-2026"

        sheet.append_row(fila)
        print(f"✅ EXITO: {producto} guardado con link de video.")

    except Exception as e:
        print(f"❌ ERROR CRÍTICO: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
