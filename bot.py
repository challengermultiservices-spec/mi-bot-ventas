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
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"  # Pon el ID de tu hoja
    TAG_ID = "chmbrand-20"    # Tu ID de Afiliado de Amazon
    # ------------------------------

    if not creds_raw:
        print("❌ Error: No se encontró la llave GOOGLE_SHEETS_CREDENTIALS")
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

        # 3. Petición Maestra a Gemini
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        
        prompt = f"""Actúa como un experto en contenido viral de TikTok Shop y Amazon. 
        Analiza los 10 productos más vendidos hoy en USA.
        Para cada producto, responde en UNA SOLA LÍNEA con este formato exacto:
        Nombre del Producto | Hook | Script de 30s (Voz en off y escenas) | Término de búsqueda para Amazon

        REGLAS PARA EL SCRIPT: Debe ser rápido, dinámico y centrado en el problema/solución.
        REGLAS PARA EL TÉRMINO: Máximo 3 palabras."""

        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
        respuesta_ia = res.json()['candidates'][0]['content']['parts'][0]['text']
        lineas = respuesta_ia.strip().split('\n')
        
        contador = 0
        for linea in lineas:
            if "|" in linea:
                datos = [d.strip() for d in linea.split('|')]
                
                if len(datos) >= 4:
                    producto = datos[0]
                    hook = datos[1]
                    script_video = datos[2]
                    termino_busqueda = datos[3].replace(" ", "+")
                    
                    # A. CONSTRUCCIÓN DEL LINK
                    link_afiliado = f"https://www.amazon.com/s?k={termino_busqueda}&tag={TAG_ID}"
                    
                    # B. GENERACIÓN DE DESCRIPCIÓN Y HASHTAGS (Automática por lógica)
                    descripcion = f"POV: You found the ultimate {producto}! ✨ Link in Bio / Check here: {link_afiliado} #amazonfinds #tiktokmade-mebuyit #viralproducts #shorts"
                    
                    # C. ESTRUCTURA FINAL PARA LA HOJA
                    # Columnas: Producto, Hook, Script, Link, Descripción Viral
                    fila_final = [producto, hook, script_video, link_afiliado, descripcion]
                    
                    sheet.append_row(fila_final)
                    contador += 1
        
        print(f"🚀 ¡Éxito! {contador} productos listos para grabar y publicar.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    ejecutar_sistema_infinito()
