import os
import requests
import json
import gspread
import time
import random
from google.oauth2.service_account import Credentials
import sys

def ejecutar_sistema_automatico():
    gemini_key = os.environ.get("GEMINI_API_KEY")
    creatomate_key = os.environ.get("CREATOMATE_API_KEY")
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    categorias = ["Hogar y Cocina", "Tecnología y Gadgets", "Mascotas", "Fitness", "Herramientas", "Belleza"]
    categoria_elegida = random.choice(categorias)

    # Lista de modelos por orden de prioridad
    modelos_a_probar = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-2.0-flash"
    ]

    try:
        print("--- Conectando a Google Sheets ---")
        creds_json = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_json, scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        client = gspread.authorize(creds)
        sheet = client.open_by_key(ID_HOJA).get_worksheet(0)

        res_g = None
        for modelo in modelos_a_probar:
            print(f"--- Probando con modelo: {modelo} ---")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={gemini_key}"
            payload = {"contents": [{"parts": [{"text": f"Dame un producto de Amazon de {categoria_elegida}. Responde: NOMBRE | BUSQUEDA | HOOK | SCRIPT"}]}]}
            
            try:
                response = requests.post(url, json=payload, timeout=30)
                temp_res = response.json()
                if 'candidates' in temp_res:
                    res_g = temp_res
                    break
                else:
                    print(f"⚠️ Modelo {modelo} sin cuota o no disponible.")
            except:
                continue

        if not res_g:
            print("❌ Ningún modelo tiene cuota disponible ahora mismo. Inténtalo en 1 hora.")
            sys.exit(1)

        # Procesar y enviar a Creatomate
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

        # Guardar en Sheets (Fila con 21 columnas para llegar a la U)
        fila = [""] * 21 
        fila[0], fila[1], fila[2], fila[20] = producto, link_afiliado, video_final_url, "chmbrand-20"
        sheet.append_row(fila)
        print(f"✅ ÉXITO: {producto} guardado en Columna A y código en Columna U.")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
