import os, requests, json, gspread, time, random, sys
from google.oauth2.service_account import Credentials

def ejecutar_sistema_automatico():
    gemini_key = os.environ.get("GEMINI_API_KEY")
    creatomate_key = os.environ.get("CREATOMATE_API_KEY")
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    categorias = ["Mascotas", "Hogar Inteligente", "Gadgets Tech", "Cocina"]
    cat = random.choice(categorias)
    
    # Usamos los nombres de modelos oficiales para la versión v1
    modelos = ["gemini-1.5-pro", "gemini-1.5-flash"]

    try:
        print(f"--- Ejecución PRO Tier 1 | Categoría: {cat} ---")
        creds = Credentials.from_service_account_info(json.loads(creds_raw), 
            scopes=['[https://www.googleapis.com/auth/spreadsheets](https://www.googleapis.com/auth/spreadsheets)', '[https://www.googleapis.com/auth/drive](https://www.googleapis.com/auth/drive)'])
        sheet = gspread.authorize(creds).open_by_key(ID_HOJA).get_worksheet(0)

        res_g = None
        for m in modelos:
            print(f"--- Solicitando a {m} vía v1 estable... ---")
            url = f"[https://generativelanguage.googleapis.com/v1/models/](https://generativelanguage.googleapis.com/v1/models/){m}:generateContent?key={gemini_key}"
            p = {"contents": [{"parts": [{"text": f"Eres un experto en Amazon. Sugiere un producto viral de {cat}. Responde únicamente con este formato: NOMBRE | BUSQUEDA | HOOK | SCRIPT"}]}]}
            
            r = requests.post(url, json=p)
            res_json = r.json()

            if 'candidates' in res_json:
                res_g = res_json
                print(f"✅ ¡Conexión exitosa con {m}!")
                break
            else:
                error_msg = res_json.get('error', {}).get('message', 'Error desconocido')
                print(f"⚠️ {m} no disponible: {error_msg}")

        if not res_g:
            print("❌ No se pudo obtener respuesta de la API v1. Revisa tu facturación en Google Cloud.")
            sys.exit(1)

        # Limpieza de la respuesta (quitamos posibles comillas de código)
        t = res_g['candidates'][0]['content']['parts'][0]['text'].replace('```', '').strip()
        d = [x.strip() for x in t.split('|')]
        
        if len(d) < 4:
            print(f"❌ Formato de respuesta insuficiente: {t}")
            sys.exit(1)

        link = f"https://www.amazon.com/s?k={d[1].replace(' ', '+')}&tag={AMAZON_TAG}"
        
        print(f"--- Renderizando Video: {d[0]} ---")
        res_c = requests.post("https://api.creatomate.com/v2/renders", 
            headers={"Authorization": f"Bearer {creatomate_key}"}, 
            json={"template_id": TEMPLATE_ID, "modifications": {"Text-1.text": d[2].upper(), "Text-2.text": d[3]}})
        
        # Guardado final
        sheet.append_row([d[0], link, res_c.json()[0]['url']])
        print(f"🚀 ¡ÉXITO! Fila añadida correctamente.")

    except Exception as e:
        print(f"❌ Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
