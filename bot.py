import os
import requests
import json
import gspread
from google.oauth2.service_account import Credentials

def ejecutar_sistema_infinito():
    api_key = os.environ.get("GEMINI_API_KEY")
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    
    if not creds_raw:
        print("❌ Error: Secret GOOGLE_SHEETS_CREDENTIALS no configurado.")
        return

    creds_json = json.loads(creds_raw)
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(creds_json, scopes=scope)
    client = gspread.authorize(creds)
    
    # --- CAMBIO AQUÍ: USA EL ID EN LUGAR DEL NOMBRE ---
    # Pega aquí el ID largo de tu URL entre las comillas
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ" 
    
    try:
        # Intentamos abrir por ID para evitar errores de nombre
        spreadsheet = client.open_by_key(ID_HOJA)
        sheet = spreadsheet.get_worksheet(0) # Abre la primera pestaña
        print(f"✅ Conectado exitosamente a: {spreadsheet.title}")
        
        # El resto del código de Gemini...
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        prompt = "Dame 3 productos de cocina virales en TikTok Shop USA. Formato: Producto | Por qué | Hook"
        
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
        texto_ia = res.json()['candidates'][0]['content']['parts'][0]['text']
        
        lineas = texto_ia.strip().split('\n')
        for linea in lineas:
            if "|" in linea:
                sheet.append_row([d.strip() for d in linea.split('|')])
        
        print("🚀 Datos guardados.")

    except gspread.exceptions.SpreadsheetNotFound:
        print("❌ Error: No se encontró la hoja. ¿Compartiste el acceso con el correo del JSON?")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    ejecutar_sistema_infinito()
