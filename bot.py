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
        creds = Credentials.from_service_account_info(creds_json, scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        client = gspread.authorize(creds)
        sheet = client.open_by_key(ID_HOJA).get_worksheet(0)

        # 2. Gemini: Generar contenido
        url_gemini = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={gemini_key}"
        prompt_texto = "Dame un producto viral de cocina para TikTok. Responde solo: NOMBRE | BUSQUEDA | HOOK | SCRIPT"
        
        response = requests.post(url_gemini, json={"contents": [{"parts": [{"text": prompt_texto}]}]})
        res_g = response.json()

        if 'candidates' not in res_g:
            print(f"❌ Error Gemini: {res_g}")
            return

        texto_respuesta = res_g['candidates'][0]['content']['parts'][0]['text']
        datos = [d.strip() for d in texto_respuesta.split('|')]
        
        if len(datos) < 4:
            print("❌ Formato de respuesta incompleto")
            return

        producto, busqueda, hook, cuerpo = datos[0], datos[1], datos[2], datos[3]

        # 3. Link de Amazon y Creatomate
        link_afiliado = f"https://www.amazon.com/s?k={busqueda.replace(' ', '+')}&tag={AMAZON_TAG}"
        
        headers_c = {"Authorization": f"Bearer {creatomate_key}", "Content-Type": "application/json"}
        payload_c = {
            "template_id": TEMPLATE_ID,
            "modifications": {
                "Text-1.text": hook.upper(),
                "Text-2.text": cuerpo
            }
        }
        
        print(f"🎬 Solicitando video para: {producto}...")
        res_c = requests.post("https://api.creatomate.com/v2/renders", headers=headers_c, json=payload_c)
        
        if res_c.status_code != 200:
            print(f"❌ Error Creatomate: {res_c.text}")
            return

        video_final_url = res_c.json()[0]['url']

        # 4. Guardar en Sheets (Columna U es la 21)
        # Llenamos una fila de 21 columnas
        fila = [""] * 21 
        fila[0] = producto        # Columna A
        fila[1] = link_afiliado  # Columna B
        fila[2] = video_final_url # Columna C
        fila[20] = "AUTO-2026"     # Columna U (Índice 20)

        sheet.append_row(fila)
        
        print(f"✅ ¡Éxito! Producto: {producto}")
        print(f"🔗 Video: {video_final_url}")

    except Exception as e:
        print(f"❌ Error crítico: {str(e)}")

if __name__ == "__main__":
    ejecutar_sistema_automatico()
