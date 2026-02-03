import os, requests, json, gspread, time, random, sys
from google.oauth2.service_account import Credentials

def ejecutar_sistema_automatico():
    gemini_key = os.environ.get("GEMINI_API_KEY")
    creatomate_key = os.environ.get("CREATOMATE_API_KEY")
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    categorias = ["Gadgets Tech", "Hogar Inteligente", "Cocina", "Mascotas"]
    cat = random.choice(categorias)

    # Lista de intentos: (Versión API, Nombre Modelo)
    intentos_api = [
        ("v1", "gemini-1.5-flash"), 
        ("v1beta", "gemini-1.5-pro"),
        ("v1beta", "gemini-2.0-flash")
    ]

    try:
        print("--- Conectando a Google Sheets ---")
        creds_info = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_info, 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        client = gspread.authorize(creds)
        sheet = client.open_by_key(ID_HOJA).get_worksheet(0)
        print("✅ Conexión con Sheets exitosa.")

        res_g = None
        for api_ver, model_name in intentos_api:
            print(f"--- Probando {model_name} en {api_ver} ---")
            url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model_name}:generateContent?key={gemini_key}"
            prompt = f"Producto Amazon viral {cat}. Responde SOLO: NOMBRE | BUSQUEDA | HOOK | SCRIPT"
            
            r = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
            res_json = r.json()
            
            if 'candidates' in res_json:
                res_g = res_json
                print(f"✅ Éxito con {model_name}")
                break
            else:
                print(f"⚠️ {model_name} falló. Continuando...")

        if not res_g:
            print(f"❌ Error final: Ningún modelo respondió. Log: {res_json}")
            sys.exit(1)

        # Extracción de datos
        texto_raw = res_g['candidates'][0]['content']['parts'][0]['text']
        lineas = texto_raw.replace('```', '').replace('markdown', '').strip().split('\n')
        datos = []
        for l in lineas:
            if '|' in l:
                datos = [x.strip() for x in l.split('|')]
                break
        
        if len(datos) < 4:
            print(f"❌ Formato inválido en: {texto_raw}")
            sys.exit(1)

        producto, busqueda, hook, cuerpo = datos[0], datos[1], datos[2], datos[3]
        link_afiliado = f"[https://www.amazon.com/s?k=](https://www.amazon.com/s?k=){busqueda.replace(' ', '+')}&tag={AMAZON_TAG}"
        
        # Renderizado Creatomate
        print(f"--- Renderizando Video: {producto} ---")
        api_url = "[https://api.creatomate.com/v2/renders](https://api.creatomate.com/v2/renders)"
        headers = {"Authorization": f"Bearer {creatomate_key}", "Content-Type": "application/json"}
        payload = {
            "template_id": TEMPLATE_ID,
            "modifications": {"Text-1.text": hook.upper(), "Text-2.text": cuerpo}
        }
        
        res_v = requests.post(api_url, headers=headers, json=payload)
        video_url = res_v.json()[0]['url']

        # Guardado
        sheet.append_row([producto, link_afiliado, video_url])
        print(f"🚀 PROCESO COMPLETADO. Fila añadida para: {producto}")

    except Exception as e:
        print(f"❌ Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
