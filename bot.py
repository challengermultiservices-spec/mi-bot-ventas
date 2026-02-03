import os
import requests
import json
import gspread
from google.oauth2.service_account import Credentials

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
        creds_json = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_json, scopes=['https://www.googleapis.com/auth/spreadsheets'])
        client = gspread.authorize(creds)
        sheet = client.open_by_key(ID_HOJA).get_worksheet(0)

        # 2. Gemini con Prompt Suave (para evitar el error 'candidates')
        url_gemini = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={gemini_key}"
        # Forzamos una respuesta simple sin temas sensibles
        prompt_texto = "Dame un producto para el hogar que sea tendencia. Formato: NOMBRE | BUSQUEDA | HOOK | SCRIPT"
        
        response = requests.post(url_gemini, json={"contents": [{"parts": [{"text": prompt_texto}]}]})
        res_g = response.json()

        # DEPURACIÓN: Si falla, esto nos dirá por qué en la consola de GitHub
        if 'candidates' not in res_g:
            print("❌ Error de Gemini. Respuesta completa del servidor:")
            print(json.dumps(res_g, indent=2))
            return

        texto_respuesta = res_g['candidates'][0]['content']['parts'][0]['text']
        datos = [d.strip() for d in texto_respuesta.split('|')]
        
        if len(datos) < 4:
            print(f"❌ Gemini devolvió un formato incorrecto: {texto_respuesta}")
            return

        producto, busqueda, hook, cuerpo = datos[0], datos[1], datos[2], datos[3]

        # 3. Link y Creatomate
        link_afiliado = f"https://www.amazon.com/s?k={busqueda.replace(' ', '+')}&tag={AMAZON_TAG}"
        
        headers_c = {"Authorization": f"Bearer {creatomate_key}", "Content-Type": "application/json"}
        payload_c = {
            "template_id": TEMPLATE_ID,
            "modifications": {
                "Text-1.text": hook.upper(),
                "Text-2.text": cuerpo
            }
        }
        
        res_c = requests.post("https://api.creatomate.com/v2/renders", headers=headers_c, json=payload_c)
        
        if res_c.status_code != 200:
            print(f"❌ Error en Creatomate: {res_c.text}")
            return

        video_final_url = res_c.json()[0]['url']

        # 4. Guardar en Sheets (Columna U es la 21)
        fila = [""] * 21 
        fila[0] = producto       # A
        fila[1] = link_afiliado # B
        fila[2] = video_final_url # C
        fila[20] = "AUTO-2026"    # U (Código Único)

        sheet.append_row(fila
