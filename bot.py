import os
import requests
import json
import gspread
import time
import random
from google.oauth2.service_account import Credentials
import sys

def ejecutar_sistema_automatico():
    # 1. Configuración de credenciales
    gemini_key = os.environ.get("GEMINI_API_KEY")
    creatomate_key = os.environ.get("CREATOMATE_API_KEY")
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    categorias = [
        "Gadgets de Cocina", "Tecnología para el hogar", "Accesorios para Mascotas", 
        "Fitness", "Herramientas", "Belleza"
    ]
    categoria_elegida = random.choice(categorias)

    # Modelos para rotar en caso de error de cuota
    modelos_a_probar = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"]

    try:
        print("--- Conectando a Google Sheets ---")
        creds_json = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_json, scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        client = gspread.authorize(creds)
        sheet = client.open_by_key(ID_HOJA).get_worksheet(0)

        res_g = None
        for modelo in modelos_a_probar:
            print(f"--- Intentando con {modelo} ---")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={gemini_key}"
            prompt = f"Sugiere un producto viral de Amazon de {categoria_elegida}. Responde estrictamente: NOMBRE | BUSQUEDA | HOOK | SCRIPT"
            
            try:
                response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
                temp_res = response.json()
                if 'candidates' in temp_res:
                    res_g = temp_res
                    break
            except:
                continue

        if not res_g:
            print("❌ Cuota agotada en todos los modelos.")
            sys.exit(1)

        # 2. Procesar respuesta
        texto = res_g['candidates'][0]['content']['parts'][0]['text']
        datos = [d.strip() for d in texto.split('|')]
        producto, busqueda, hook, cuerpo = datos[0], datos[1], datos[2], datos[3]
        link_afiliado = f"https://www.amazon.com/s?k={busqueda.replace(' ', '+')}&tag={AMAZON_TAG}"

        # 3. Creatomate
        print(f"--- Generando Video para: {producto} ---")
        headers = {"Authorization": f"Bearer {creatomate_key}", "Content-Type": "application/json"}
        payload = {
            "template_id": TEMPLATE_ID,
            "modifications": {
                "Text-1.text": hook.upper(),
                "Text-2.text": cuerpo
            }
        }
        res_c = requests.post("https://api.creatomate.com/v2/renders", headers=headers, json=payload)
        video_url = res_c.json()[0]['url']

        # 4. Guardar en Sheets (Solo Columnas A, B, C)
        fila = [producto, link_afiliado, video_url]
        sheet.append_row(fila)
        
        print(f"✅ ÉXITO: {producto} guardado.")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
