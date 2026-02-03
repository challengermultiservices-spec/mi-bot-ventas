import os, requests, json, gspread, time, random, sys
from google.oauth2.service_account import Credentials

def ejecutar_sistema_automatico():
    gemini_key = os.environ.get("GEMINI_API_KEY")
    creatomate_key = os.environ.get("CREATOMATE_API_KEY")
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    categorias = ["Gadgets Tech", "Hogar Inteligente", "Mascotas", "Cocina"]
    cat = random.choice(categorias)
    
    # Probamos v1beta que es la más flexible para cuentas nuevas PRO
    modelos = ["gemini-1.5-pro", "gemini-1.5-flash"]

    try:
        print(f"--- Ejecución PRO | Categoría: {cat} ---")
        creds = Credentials.from_service_account_info(json.loads(creds_raw), 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        sheet = gspread.authorize(creds).open_by_key(ID_HOJA).get_worksheet(0)

        res_g = None
        for m in modelos:
            print(f"--- Intentando con {m}... ---")
            # Cambiamos a v1beta para asegurar compatibilidad inicial
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={gemini_key}"
            p = {"contents": [{"parts": [{"text": f"Sugiere un producto viral de Amazon de {cat}. Responde: NOMBRE | BUSQUEDA | HOOK | SCRIPT"}]}]}
            
            r = requests.post(url, json=p)
            res_json = r.json()

            if 'candidates' in res_json:
                res_g = res_json
                print(f"✅ ¡Éxito con {m}!")
                break
            else:
                # Esto nos dirá el error REAL de Google
                msg = res_json.get('error', {}).get('message', 'Error desconocido')
                print(f"⚠️ {m} falló. Motivo: {msg}")

        if not res_g:
            print("❌ No se pudo obtener respuesta. Verifica que la API Key en GitHub sea la nueva del Tier 1.")
            sys.exit(1)

        t = res_g['candidates'][0]['content']['parts'][0]['text']
        d = [x.strip() for x in t.split('|')]
        link = f"https://www.amazon.com/s?k={d[1].replace(' ', '+')}&tag={AMAZON_TAG}"
        
        print(f"--- Renderizando Video: {d[0]} ---")
        res_c = requests.post("https://api.creatomate.com/v2/renders", 
            headers={"Authorization": f"Bearer {creatomate_key}"}, 
            json={"template_id": TEMPLATE_ID, "modifications": {"Text-1.text": d[2].upper(), "Text-2.text": d[3]}})
        
        sheet.append_row([d[0], link, res_c.json()[0]['url']])
        print(f"🚀 ¡LOGRADO! Fila agregada.")

    except Exception as e:
        print(f"❌ Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
