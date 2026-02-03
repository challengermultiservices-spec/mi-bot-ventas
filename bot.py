import os, requests, json, gspread, time, random, sys
from google.oauth2.service_account import Credentials

def ejecutar_sistema_automatico():
    # 1. Configuración de credenciales
    gemini_key = os.environ.get("GEMINI_API_KEY")
    creatomate_key = os.environ.get("CREATOMATE_API_KEY")
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    # Categorías premium para mejores conversiones
    categorias = ["Hogar Inteligente", "Gadgets de Cocina", "Cuidado Personal", "Mascotas", "Oficina en Casa"]
    cat = random.choice(categorias)
    
    # Modelos optimizados para el plan Pay-as-you-go
    modelos = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash"]

    try:
        print(f"--- Iniciando proceso PRO (Categoría: {cat}) ---")
        creds = Credentials.from_service_account_info(json.loads(creds_raw), scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        sheet = gspread.authorize(creds).open_by_key(ID_HOJA).get_worksheet(0)

        res_g = None
        for m in modelos:
            print(f"--- Solicitando a {m} ---")
            # Intentamos primero con la versión estable v1 (ideal para PRO)
            url = f"https://generativelanguage.googleapis.com/v1/models/{m}:generateContent?key={gemini_key}"
            prompt = f"Actúa como un experto en marketing de Amazon. Sugiere un producto viral de {cat}. Responde estrictamente: NOMBRE | BUSQUEDA | HOOK | SCRIPT"
            
            r = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
            res_json = r.json()

            if 'candidates' in res_json:
                res_g = res_json
                print(f"✅ Respuesta exitosa de {m}")
                break
            else:
                # Si falla, reintento rápido con v1beta
                url_beta = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={gemini_key}"
                r_beta = requests.post(url_beta, json={"contents": [{"parts": [{"text": prompt}]}]})
                res_beta = r_beta.json()
                if 'candidates' in res_beta:
                    res_g = res_beta
                    print(f"✅ Respuesta exitosa de {m} (v1beta)")
                    break
                print(f"⚠️ {m} no respondió correctamente.")

        if not res_g:
            print("❌ No se pudo conectar con ningún modelo. Revisa tu nueva API Key en GitHub.")
            sys.exit(1)

        # 2. Procesar respuesta
        t = res_g['candidates'][0]['content']['parts'][0]['text']
        d = [x.strip() for x in t.split('|')]
        if len(d) < 4:
            print(f"❌ Formato de Gemini incorrecto: {t}")
            sys.exit(1)

        link = f"https://www.amazon.com/s?k={d[1].replace(' ', '+')}&tag={AMAZON_TAG}"

        # 3. Creatomate
        print(f"--- Generando Video en Creatomate: {d[0]} ---")
        res_c = requests.post("https://api.creatomate.com/v2/renders", 
            headers={"Authorization": f"Bearer {creatomate_key}"}, 
            json={
                "template_id": TEMPLATE_ID, 
                "modifications": {
                    "Text-1.text": d[2].upper(), 
                    "Text-2.text": d[3]
                }
            })
        
        if res_c.status_code not in [200, 201]:
            print(f"❌ Error Creatomate: {res_c.text}")
            sys.exit(1)

        video_url = res_c.json()[0]['url']

        # 4. Guardar en Sheets (Columnas A, B, C)
        sheet.append_row([d[0], link, video_url])
        print(f"🚀 ¡EXITO! Producto guardado con código chmbrand-20.")

    except Exception as e:
        print(f"❌ Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
