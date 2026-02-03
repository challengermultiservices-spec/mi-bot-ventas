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

    try:
        # Conexión a Sheets
        print("--- Conectando a Google Sheets ---")
        creds_json = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_json, scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        client = gspread.authorize(creds)
        sheet = client.open_by_key(ID_HOJA).get_worksheet(0)

        # 2. Gemini: Intento con URL Estable v1
        print("--- Pidiendo producto a Gemini ---")
        # Cambiamos a la URL que suele ser la más compatible ahora mismo
        url_gemini = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={gemini_key}"
        
        payload_gemini = {
            "contents": [{"parts": [{"text": "Dame un producto viral de Amazon. Responde solo: NOMBRE | BUSQUEDA | HOOK | SCRIPT"}]}]
        }
        
        response = requests.post(url_gemini, json=payload_gemini)
        res_g = response.json()

        # Si falla la v1, intentamos con un nombre de modelo alternativo
        if 'error' in res_g:
            print("--- Reintentando con configuración alternativa ---")
            url_gemini = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={gemini_key}"
            response = requests.post(url_gemini, json=payload_gemini)
            res_g = response.json()

        if 'candidates' not in res_g:
            print(f"❌ Error Gemini detallado: {json.dumps(res_g, indent=2)}")
            sys.exit(1)

        texto_respuesta = res_g['candidates'][0]['content']['parts'][0]['text']
        datos = [d.strip() for d in texto_respuesta.split('|')]
        
        if len(datos) < 4:
            print(f"❌ Formato de Gemini incorrecto: {texto_respuesta}")
            sys.exit(1)

        producto, busqueda, hook, cuerpo = datos[0], datos[1], datos[2], datos[3]

        # 3. Amazon Link y Creatomate
        link_afiliado = f"https://www.amazon.com/s?k={busqueda.replace(' ', '+')}&tag={AMAZON_TAG}"
        
        print(f"--- Enviando a Creatomate: {producto} ---")
        headers_c = {"Authorization": f
