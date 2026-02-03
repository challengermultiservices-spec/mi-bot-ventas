import os
import requests
import json
import gspread
from google.oauth2.service_account import Credentials

def ejecutar_sistema_infinito():
    # 1. Configuración de Credenciales
    api_key = os.environ.get("GEMINI_API_KEY")
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    
    # --- CONFIGURACIÓN PERSONAL ---
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"  # El ID de tu URL de Google Sheets
    TAG_ID = "chmbrand-20"    # Tu ID de Afiliado de Amazon
    # ------------------------------

    if not creds_raw:
        print("❌ Error: No se encontró la llave GOOGLE_SHEETS_CREDENTIALS en Secrets")
        return

    try:
        # 2. Conexión con Google Sheets
        creds_json = json.loads(creds_raw)
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_json, scopes=scope)
        client = gspread.authorize(creds)
        
        spreadsheet = client.open_by_key(ID_HOJA)
        sheet = spreadsheet.get_worksheet(0)
        print(f"✅ Conectado a: {spreadsheet.title}")

        # 3. Petición a Gemini 2.5 Flash
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        
        prompt = """Actúa como un experto en E-commerce. Analiza los 10 productos más vendidos y virales en TikTok Shop y Amazon USA hoy.
        Para cada producto, responde estrictamente en una sola línea con este formato:
        Nombre del Producto | Por qué es Viral | Hook de Venta | Término de búsqueda corto para Amazon"""

        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
        
        if res.status_code != 200:
            print(f"❌ Error de API Gemini: {res.text}")
            return

        respuesta_ia = res.json()['candidates'][0]['content']['parts'][0]['text']
        lineas = respuesta_ia.strip().split('\n')
        
        # 4. Procesamiento y Construcción de Links
        contador = 0
        for linea in lineas:
            if "|" in linea:
                # Separar los datos por el caracter "|"
                datos = [d.strip() for d in linea.split('|')]
                
                if len(datos) >= 4:
                    nombre_producto = datos[0]
                    por_que = datos[1]
                    hook = datos[2]
                    termino_busqueda = datos[3].replace(" ", "+")
                    
                    # CONSTRUCCIÓN DEL LINK DE AFILIADO
                    link_afiliado = f"https://www.amazon.com/s?k={termino_busqueda}&tag={TAG_ID}"
                    
                    # Preparar la fila para Google Sheets
                    # Formato final: [Producto, Por qué, Hook, Link]
                    fila_final = [nombre_producto, por_que, hook, link_afiliado]
                    
                    sheet.append_row(fila_final)
                    contador += 1
        
        print(f"🚀 ¡Éxito! Se han añadido {contador} productos con sus links de afiliado.")

    except Exception as e:
        print(f"❌ Error durante la ejecución: {e}")

if __name__ == "__main__":
    ejecutar_sistema_infinito()
