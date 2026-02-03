import os
import requests
import json
import gspread
import time
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

        # 2. Gemini con Reintento por Cuota (429)
        print("--- Pidiendo producto a Gemini 2.0 Flash ---")
        url_gemini = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
        payload_gemini = {"contents": [{"parts": [{"text": "Dame un producto viral de Amazon. Responde: NOMBRE | BUSQUEDA | HOOK | SCRIPT"}]}]}
        
        for intento in range(3):
            response = requests.post(url_gemini, json=payload_gemini)
            res_g = response.json()
            
            if 'error' in res_g and res_g['error']['code'] == 429:
                print(f"⚠️ Cuota agotada. Reintentando en 60 segundos (Intento {intento+1}/3)...")
                time.sleep(65)
                continue
            break

        if 'candidates' not in res_g:
            print(f"❌ Error final Gemini: {json.dumps(res_g)}")
            sys.exit(1)

        # 3. Procesar y Enviar a Creatomate
        texto_respuesta = res_g['candidates'][0]['content']['parts'][0]['text']
        datos = [d.strip() for d in texto_respuesta.split('|')]
        producto, busqueda, hook, cuerpo = datos[0], datos[1], datos[2], datos[3]

        link_afiliado = f"https://www.amazon.com/s?k={busqueda.replace(' ', '+')}&tag={AMAZON_TAG}"
        
        print(f"--- Generando Video para: {producto} ---")
        headers_c = {"Authorization": f"Bearer {creatomate_key}", "Content-Type": "application/json"}
        payload_c = {
            "template_id": TEMPLATE_ID,
            "modifications": {"Text-1.text": hook.upper(), "Text-2.text": cuerpo}
        }
        
        res_c = requests.post("https://api.creatomate.com/v2/renders", headers=headers_c, json=payload_c)
        video_final_url = res_c.json()[0]['url']

        # 4. Guardar en Sheets
        fila = [""] * 21 
        fila[0], fila[1], fila[2], fila[20] = producto, link_afiliado, video_final_url, "AUTO-2026"
        sheet.append_row(fila)
        
        print(f"✅ ¡ÉXITO! Producto guardado con código chmbrand-20.")

    except Exception as e:
        print(f"❌ Error Crítico: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
