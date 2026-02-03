import os, requests, json, gspread, time, random, sys
from google.oauth2.service_account import Credentials

def ejecutar_sistema_automatico():
    gemini_key = os.environ.get("GEMINI_API_KEY")
    creatomate_key = os.environ.get("CREATOMATE_API_KEY")
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    categorias = ["Hogar Inteligente", "Gadgets Tech", "Cocina", "Mascotas"]
    cat = random.choice(categorias)

    try:
        print("--- Conectando a Google Sheets ---")
        creds_info = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_info, 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        client = gspread.authorize(creds)
        sheet = client.open_by_key(ID_HOJA).get_worksheet(0)
        print("✅ Conexión con Sheets exitosa.")

        print(f"--- Solicitando a Gemini Pro (Categoría: {cat}) ---")
        url_gemini = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={gemini_key}"
        
        # Prompt más estricto y con ejemplo
        prompt = (f"Sugiere un producto viral de Amazon de la categoría {cat}. "
                  "Responde ÚNICAMENTE en este formato: NOMBRE | TERMINO_BUSQUEDA | HOOK | CUERPO_GUION. "
                  "No añadas introducciones ni explicaciones.")
        
        r = requests.post(url_gemini, json={"contents": [{"parts": [{"text": prompt}]}]})
        res_json = r.json()
        
        if 'candidates' not in res_json:
            print(f"❌ Error API Gemini: {res_json}"); sys.exit(1)

        # Lógica de extracción mejorada
        texto_raw = res_json['candidates'][0]['content']['parts'][0]['text']
        print(f"DEBUG: Respuesta recibida: {texto_raw}")

        # Limpiamos posibles formatos markdown o saltos de línea
        lineas = texto_raw.replace('```', '').replace('markdown', '').strip().split('\n')
        
        # Buscamos la línea que contenga los separadores '|'
        datos_procesados = []
        for linea in lineas:
            if '|' in linea:
                datos_procesados = [x.strip() for x in linea.split('|')]
                break
        
        if len(datos_procesados) < 4:
            print(f"❌ Error: No se detectaron 4 columnas. Datos: {datos_procesados}")
            sys.exit(1)

        producto, busqueda, hook, cuerpo = datos_procesados[0], datos_procesados[1], datos_procesados[2], datos_procesados[3]
        link_afiliado = f"[https://www.amazon.com/s?k=](https://www.amazon.com/s?k=){busqueda.replace(' ', '+')}&tag={AMAZON_TAG}"
        
        print(f"--- Renderizando Video: {producto} ---")
        api_url = "[https://api.creatomate.com/v2/renders](https://api.creatomate.com/v2/renders)"
        headers = {"Authorization": f"Bearer {creatomate_key}", "Content-Type": "application/json"}
        payload = {
            "template_id": TEMPLATE_ID,
            "modifications": {
                "Text-1.text": hook.upper(),
                "Text-2.text": cuerpo
            }
        }
        
        res_v = requests.post(api_url, headers=headers, json=payload)
        video_url = res_v.json()[0]['url']

        # Guardado final
        sheet.append_row([producto, link_afiliado, video_url])
        print(f"🚀 PROCESO COMPLETADO. Fila añadida para: {producto}")

    except Exception as e:
        print(f"❌ Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
