import os
import requests
import json
import gspread
from google.oauth2.service_account import Credentials

def ejecutar_sistema_infinito():
    # 1. Cargar credenciales desde los Secrets de GitHub
    api_key = os.environ.get("GEMINI_API_KEY")
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    
    if not creds_raw:
        print("❌ Error: No se encontró la llave GOOGLE_SHEETS_CREDENTIALS")
        return

    creds_json = json.loads(creds_raw)
    
    # 2. Configurar permisos de Google
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(creds_json, scopes=scope)
    client = gspread.authorize(creds)
    
    # 3. Abrir tu Google Sheets
    # CAMBIA "Nombre de tu Hoja" por el nombre real de tu archivo de Sheets
    try:
        sheet = client.open("Nombre de tu Hoja").sheet1
        print("✅ Conectado a Google Sheets")
    except Exception as e:
        print(f"❌ Error al abrir la hoja: {e}")
        return

    # 4. Obtener tendencia de Gemini 2.5 Flash
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    prompt = "Dame 3 productos de cocina virales en TikTok Shop USA hoy. Responde SOLO en este formato: Producto | Por qué es viral | Hook"
    
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
        respuesta = res.json()
        texto_ia = respuesta['candidates'][0]['content']['parts'][0]['text']
        
        # 5. Escribir en la hoja (Creación infinita de filas)
        lineas = texto_ia.strip().split('\n')
        for linea in lineas:
            if "|" in linea:
                datos = [d.strip() for d in linea.split('|')]
                sheet.append_row(datos)
        
        print(f"🚀 ¡Éxito! Se han añadido {len(lineas)} tendencias a tu hoja.")

    except Exception as e:
        print(f"❌ Error en el proceso: {e}")

if __name__ == "__main__":
    ejecutar_sistema_infinito()
