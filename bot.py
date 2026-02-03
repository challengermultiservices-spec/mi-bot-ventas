import os, requests, json, gspread, time, random, sys
from google.oauth2.service_account import Credentials

def ejecutar_sistema_automatico():
    gemini_key = os.environ.get("GEMINI_API_KEY")
    creatomate_key = os.environ.get("CREATOMATE_API_KEY")
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    categorias = ["Hogar Inteligente", "Gadgets Tech", "Mascotas", "Cocina"]
    cat = random.choice(categorias)
    
    # Modelos en orden de estabilidad para cuentas de pago
    modelos = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash"]

    try:
        print(f"--- Iniciando proceso PRO para categoría: {cat} ---")
        creds = Credentials.from_service_account_info(json.loads(creds_raw), scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        client = gspread.authorize(creds)
        sheet = client.open_by_key(ID_HOJA).get_worksheet(0)

        res_g = None
        for m in modelos:
            print(f"--- Consultando a {m} ---")
            # Usamos la URL estable v1 para el plan de pago
            url = f"https://generativelanguage.googleapis.com/v1/models/{m}:generateContent?key={gemini_key}"
            p = {"contents": [{"parts": [{"text": f"Sugiere un producto viral de Amazon de {cat}. Responde solo: NOMBRE | BUSQUEDA | HOOK | SCRIPT"}]}]}
            
            r = requests.post(url, json=p)
            res_json = r.json()

            if 'candidates' in res_json:
                res_g = res_json
                print(f"✅ Respuesta exitosa de {m}")
                break
            else:
                # Si falla v1, intentamos v1beta automáticamente
                url_beta = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={gemini_key}"
                r_beta = requests.post(url_beta, json=p)
                res_beta = r_beta.json()
                if 'candidates' in res_beta:
                    res_g = res_beta
                    print(f"✅ Respuesta exitosa de {m} (v1beta)")
                    break
                print(f"⚠️ {m} no respondió: {res_beta.get('error', {}).get('message', 'Error desconocido')}")

        if not res_g:
            print("❌ No se pudo obtener respuesta de ningún modelo. Verifica que tu nueva API KEY esté en GitHub Secrets.")
            sys.exit(1)

        t = res_g['candidates'][0]['content']['parts'][0]['text']
        d = [x.strip() for x in t.split('|')]
        link = f"https://www.amazon.com/s?k={d[1].replace(' ', '+')}&tag={AMAZON_TAG}"

        print(f"--- Enviando a Creatomate: {d[0]} ---")
        res_c = requests.post("https://api.creatomate.com/v2/renders", 
            headers={"Authorization": f"Bearer {creatomate_key}"}, 
            json={
                "template_id": TEMPLATE_ID, 
                "modifications": {"Text-1.text": d[2].upper(), "Text-2.text": d[3]}
            })
        
        # Guardar en Sheets (A, B, C)
        sheet.append_row([d[0], link, res_c.json()[0]['url']])
        print(f"🚀 ¡LOGRADO! Producto guardado con éxito.")

    except Exception as e:
        print(f"❌ Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
