import os
import requests
import json
import gspread
from google.oauth2.service_account import Credentials

def ejecutar_bot():
    api_key = os.environ.get("GEMINI_API_KEY")
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    TAG_ID = "chmbrand-20" 

    try:
        creds_json = json.loads(creds_raw)
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_json, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(ID_HOJA).get_worksheet(0)

        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        prompt = {
            "contents": [{
                "parts": [{"text": """Genera 10 productos virales. Para cada uno responde en una sola línea:
                NOMBRE | BUSQUEDA | PROMPT_INVIDEO | CODIGO_UNICO
                
                En PROMPT_INVIDEO crea un párrafo que pida a InVideo AI un TikTok de 30s con voz latina enérgica sobre el producto.
                En CODIGO_UNICO inventa un código alfanumérico de 5 dígitos."""}]
            }]
        }

        res = requests.post(url, json=prompt)
        res_json = res.json()

        if 'candidates' not in res_json:
            print(f"Error de API: {res_json}")
            return

        respuesta = res_json['candidates'][0]['content']['parts'][0]['text']
        lineas = [l for l in respuesta.strip().split('\n') if "|" in l]

        for linea in lineas:
            partes = [p.strip() for p in linea.split('|')]
            if len(partes) >= 4:
                nombre, busqueda, invideo_p, codigo = partes[0], partes[1], partes[2], partes[3]
                link = f"https://www.amazon.com/s?k={busqueda.replace(' ', '+')}&tag={TAG_ID}"
                
                # Creamos la fila para la hoja (llenando hasta la columna U)
                # Columna A: Nombre, B: Link, C: Prompt InVideo... U: Código Único
                nueva_fila = [""] * 21 # Crea una lista de 21 espacios (A a U)
                nueva_fila[0] = nombre        # Columna A
                nueva_fila[1] = link          # Columna B
                nueva_fila[2] = invideo_p     # Columna C
                nueva_fila[20] = codigo       # Columna U (Índice 20)
                
                sheet.append_row(nueva_fila)

        print("✅ Datos enviados a Sheets. Revisa la columna U para los códigos.")

    except Exception as e:
        print(f"❌ Error crítico: {str(e)}")

if __name__ == "__main__":
    ejecutar_bot()
