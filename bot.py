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

    # 2. Variedad de contenido
    categorias = [
        "Gadgets de Cocina", "Tecnología para el hogar", "Accesorios para Mascotas", 
        "Fitness y Deporte", "Herramientas inteligentes", "Cuidado Personal"
    ]
    categoria_elegida = random.choice(categorias)

    # 3. Lista de modelos (Ordenados por estabilidad de cuota)
    modelos_a_probar = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]

    try:
        print(f"--- Conectando a Google Sheets ---")
        creds_json = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_json, scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        client = gspread.authorize(creds)
        sheet = client.open_by_key(ID_HOJA).get_worksheet(0)

        # 4. Bucle de reintento entre modelos de Gemini
        res_g = None
        for modelo in modelos_a_probar:
            print(f"--- Intentando con {modelo} (Categoría: {categoria_elegida}) ---")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={gemini_key}"
            prompt = f"Sugiere un producto viral de Amazon de {categoria_elegida}. Responde estrictamente: NOMBRE | BUSQUEDA | HOOK | SCRIPT"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            
            response = requests.post(url, json=payload, timeout=30)
            temp_res = response.json()
            
            if 'candidates' in temp_res:
                res_g = temp_res
                print(f"✅ {modelo} respondió con éxito.")
                break
            else:
                print(f"⚠️ {modelo} falló (posible falta de cuota).")
                time.sleep(2) # Pausa breve antes de probar el siguiente modelo

        if not res_g:
            print("❌ No hay modelos disponibles hoy. La cuota de Google está agotada.")
            sys.exit(1)

        # 5. Procesar respuesta de Gemini
        texto = res_g['candidates'][0]['content']['parts'][0]['text']
        datos = [d.strip() for d in texto.split('|')]
        
        if len(datos) < 4:
            print(f"❌ Formato de respuesta inválido: {texto}")
            sys.exit(1)

        producto, busqueda, hook, cuerpo = datos[0], datos[1], datos[2], datos[3]
        link_afiliado = f"https://www.amazon.com/s?k={busqueda.replace(' ', '+')}&tag={AMAZON_TAG}"

        # 6. Creatomate: Generación de Video
        print(f"--- Generando Video en Creatomate para: {producto} ---")
        headers_c = {"Authorization": f"Bearer {creatomate_key}", "Content-Type": "application/json"}
        payload_c = {
            "template_id": TEMPLATE_ID,
            "modifications": {
                "Text-1.text": hook.upper(),
                "Text-2.text": cuerpo
            }
        }
        
        res_c = requests.post("https://api.creatomate.com/v2/renders", headers=headers_c, json=payload_c)
        video_final_url = res_c.json()[0]['url']

        # 7. Guardar en Sheets (Código en Columna U)
        # Creamos una fila de 21 espacios (A hasta U)
        fila = [""] * 21 
        fila[0] = producto        # Columna A
        fila[1] = link_afiliado   # Columna B
        fila[2] = video_final_url # Columna C
        fila[20] = "chmbrand-     # Columna U (Índice 20)

        sheet.append_row(fila)
        print(f"✅ PROCESO COMPLETADO: {producto} guardado en Sheets.")

    except Exception as e:
        print(f"❌ Error Crítico: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
