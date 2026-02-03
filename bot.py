import os, requests, json, gspread, time, random, sys
from google.oauth2.service_account import Credentials

def ejecutar_sistema_automatico():
    # 1. Credenciales y Configuración
    gemini_key = os.environ.get("GEMINI_API_KEY")
    creatomate_key = os.environ.get("CREATOMATE_API_KEY")
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    categorias = ["Hogar Inteligente", "Gadgets de Cocina", "Cuidado Personal", "Mascotas", "Oficina"]
    cat = random.choice(categorias)
    
    # Modelos prioritarios para el plan de pago
    modelos = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash"]

    try:
        print(f"--- Iniciando Proceso PRO (Categoría: {cat}) ---")
        creds = Credentials.from_service_account_info(json.loads(creds_raw), scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        sheet = gspread.authorize(creds).open_by_key(ID_HOJA).get_worksheet(0)

        res_g = None
        for m in modelos:
            print(f"--- Solicitando a {m} ---")
            # Versión estable v1 para asegurar la cuota de pago
            url = f"https://generativelanguage.googleapis.com/v1/models/{m}:generateContent?key={gemini_key}"
            prompt = f"Actúa como experto en Amazon. Sugiere un producto viral de {cat}. Responde estrictamente: NOMBRE | BUSQUEDA | HOOK | SCRIPT"
            
            r = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
            res_json = r.json()

            if 'candidates' in res_json:
                res_g = res_json
                print(f"✅ Respuesta exitosa de {m}")
                break
            else:
                # Reintento en v1beta si v1 falla
                url_beta = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={gemini_key}"
                r_beta = requests.post(url_beta, json={"contents": [{"parts": [{"text": prompt}]}]})
                res_beta = r_beta.json()
                if 'candidates' in res_beta:
                    res_g = res_beta
                    print(f"✅ Respuesta exitosa de {m} (v1beta)")
                    break
                print(f"⚠️ {m} no respondió. Continuando...")

        if not res_g:
            print("❌ No se pudo obtener respuesta de ningún modelo. Verifica tu API Key PRO en GitHub.")
            sys.exit(1)

        # 2. Procesar respuesta de Gemini
        t = res_g['candidates'][0]['content']['parts'][0]['text']
        d = [x.strip() for x in t.split('|')]
        if len(d) < 4:
            print(f"❌ Error en formato de respuesta: {t}")
            sys.exit(1)

        producto, busqueda, hook, cuerpo = d[0], d[1], d[2], d[3]
        link_afiliado = f"https://www.amazon.com/s?k={busqueda.replace(' ', '+')}&tag={AMAZON_TAG}"

        # 3. Creatomate: Renderizado de Video
        print(f"--- Renderizando Video para: {producto} ---")
        res_c = requests.post("https://api.creatomate.com/v2/renders", 
            headers={"Authorization": f"Bearer {creatomate_key}"}, 
            json={
                "template_id": TEMPLATE_ID, 
                "modifications": {
                    "Text-1.text": hook.upper(), 
                    "Text-2.text": cuerpo
                }
            })
        
        if res_c.status_code not in [200, 201]:
            print(f"❌ Error en Creatomate: {res_c.text}")
            sys.exit(1)

        video_url = res_c.json()[0]['url']

        # 4. Guardar en Sheets (A, B, C)
        sheet.append_row([producto, link_afiliado, video_url])
        print(f"🚀 ¡EXITO! {producto} guardado con link de afiliado {AMAZON_TAG}")

    except Exception as e:
        print(f"❌ Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
