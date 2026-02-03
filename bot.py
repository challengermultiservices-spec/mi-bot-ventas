import os
import requests
import json
import gspread
from google.oauth2.service_account import Credentials

def ejecutar_sistema_automatico():
    # 1. Configuración de Credenciales y IDs
    gemini_key = os.environ.get("GEMINI_API_KEY")
    creatomate_key = os.environ.get("CREATOMATE_API_KEY")
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" # <--- AQUÍ ESTÁ TU ID DE AFILIADO
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    try:
        # 2. Conexión a Google Sheets
        creds_json = json.loads(creds_raw)
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_json, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(ID_HOJA).get_worksheet(0)

        # 3. Gemini: Generar contenido viral
        url_gemini = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={gemini_key}"
        prompt_texto = "Dame el producto más viral de Amazon hoy. Responde solo en este formato: PRODUCTO | TERMINO_BUSQUEDA | HOOK | CUERPO_SCRIPT"
        
        res_g = requests.post(url_gemini, json={"contents": [{"parts": [{"text": prompt_texto}]}]}).json()
        datos = res_g['candidates'][0]['content']['parts'][0]['text'].split('|')
        
        producto = datos[0].strip()
        busqueda = datos[1].strip()
        hook = datos[2].strip()
        cuerpo = datos[3].strip()

        # 4. Crear Link de Afiliado Amazon
        link_afiliado = f"https://www.amazon.com/s?k={busqueda.replace(' ', '+')}&tag={AMAZON_TAG}"

        # 5. Creatomate: Generar Video Automático (Cero copiar/pegar)
        print(f"🎬 Generando video para {producto}...")
        headers_c = {"Authorization": f"Bearer {creatomate_key}", "Content-Type": "application/json"}
        payload_c = {
            "template_id": TEMPLATE_ID,
            "modifications": {
                "Text-1.text": hook.upper(),
                "Text-2.text": cuerpo
            }
        }
        
        res_c = requests.post("https://api.creatomate.com/v2/renders", headers=headers_c, json=payload_c)
        render_data = res_c.json()
        
        # Obtenemos el link del video generado
        video_final_url = render_data[0]['url']

        # 6. Guardar todo en Sheets (Código Único en Columna U)
        # La columna U es la posición 21 (índice 20 en Python)
        fila = [""] * 21 
        fila[0] = producto       # Columna A
        fila[1] = link_afiliado # Columna B
        fila[2] = video_final_url # Columna C (Link para descargar el video)
        fila[20] = "AF-2026"    # Columna U (Código Único)

        sheet.append_row(fila)
        print(f"✅ ¡Éxito total! Video y link de afiliado guardados.")

    except Exception as e:
        print(f"❌ Error en el proceso: {e}")

if __name__ == "__main__":
    ejecutar_sistema_automatico()
