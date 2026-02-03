import os
import requests
import json
import gspread
from google.oauth2.service_account import Credentials
import sys

def ejecutar_sistema_automatico():
    # 1. Configuración de Credenciales
    gemini_key = os.environ.get("GEMINI_API_KEY")
    creatomate_key = os.environ.get("CREATOMATE_API_KEY")
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    if not all([gemini_key, creatomate_key, creds_raw]):
        print("❌ ERROR: Faltan Secretos en GitHub (GEMINI, CREATOMATE o GOOGLE_SHEETS)")
        sys.exit(1)

    try:
        # Conexión a Sheets
        print("--- Conectando a Google Sheets ---")
        creds_json = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_json, scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        client = gspread.authorize(creds)
        sheet = client.open_by_key(ID_HOJA).get_worksheet(0)

        # 2. Gemini: URL v1beta
        print("--- Pidiendo producto a Gemini ---")
        url_gemini = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
        
        payload_gemini = {
            "contents": [{"parts": [{"text": "Dame un producto viral de Amazon. Formato: NOMBRE | BUSQUEDA | HOOK | SCRIPT"}]}]
        }
        
        response = requests.post(url_gemini, json=payload_gemini)
        res_g = response.json()

        if 'candidates' not in res_g:
            print(f"❌ Error Gemini detallado: {res_g}")
            sys.exit(1)

        texto_respuesta = res_g['candidates'][0]['content']['parts'][0]['text']
        datos = [d.strip() for d in texto_respuesta.split('|')]
        producto, busqueda, hook, cuerpo = datos[0], datos[1], datos[2], datos[3]

        # 3. Amazon Link y Creatomate
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
        
        if res_c.status_code not in [200, 201]:
            print(f"❌ Error Creatomate detallado: {res_c.text}")
            sys.exit(1)

        video_final_url = res_c.json()[0]['url']

        # 4. Guardar en Sheets (Columna U es la 21)
        fila = [""] * 21 
        fila[0] = producto
        fila[1] = link_afiliado
        fila[2] = video_final_url
        fila[20] = "AUTO-2026"

        sheet.append_row(fila)
        print(f"✅ TODO OK: {producto} guardado con link {video_final_url}")

    except Exception as e:
        print(f"❌ ERROR CRÍTICO NO ESPERADO: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
