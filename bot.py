import os, requests, json, gspread, time, random, sys
from google.oauth2.service_account import Credentials
from gspread.exceptions import APIError

def ejecutar_sistema_automatico():
    gemini_key = os.environ.get("GEMINI_API_KEY")
    creatomate_key = os.environ.get("CREATOMATE_API_KEY")
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    categorias = ["Hogar", "Gadgets Tech", "Cocina", "Mascotas"]
    cat = random.choice(categorias)

    try:
        # 1. Conexión a Sheets con Reintentos (Protección 503)
        print(f"--- Conectando a Google Sheets ---")
        creds_info = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_info, 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        
        client = gspread.authorize(creds)
        
        sheet = None
        for intento in range(3):
            try:
                sheet = client.open_by_key(ID_HOJA).get_worksheet(0)
                print("✅ Conexión con Sheets exitosa.")
                break
            except APIError as e:
                if e.response.status_code == 503:
                    print(f"⚠️ Servidor de Google ocupado (503). Reintentando en 10s... ({intento+1}/3)")
                    time.sleep(10)
                else: raise e

        if not sheet:
            print("❌ No se pudo conectar a Sheets tras varios intentos."); sys.exit(1)

        # 2. Gemini con Rotación
        print(f"--- Solicitando producto de {cat} ---")
        modelos_y_versiones = [
            ("v1beta", "gemini-1.5-pro"),
            ("v1beta", "gemini-2.0-flash"),
            ("v1", "gemini-1.5-flash")
        ]

        res_g = None
        for version, modelo in modelos_y_versiones:
            url = f"https://generativelanguage.googleapis.com/{version}/models/{modelo}:generateContent?key={gemini_key}"
            payload = {"contents": [{"parts": [{"text": f"Producto viral Amazon {cat}. Responde únicamente: NOMBRE | BUSQUEDA | HOOK | SCRIPT"}]}]}
            
            r = requests.post(url, json=payload)
            res_json = r.json()
            if 'candidates' in res_json:
                res_g = res_json
                print(f"✅ ¡Éxito con {modelo}!")
                break

        if not res_g:
            print("❌ Ningún modelo Gemini respondió."); sys.exit(1)

        t = res_g['candidates'][0]['content']['parts'][0]['text'].replace('```', '').strip()
        d = [x.strip() for x in t.split('|')]
        link = f"[https://www.amazon.com/s?k=](https://www.amazon.com/s?k=){d[1].replace(' ', '+')}&tag={AMAZON_TAG}"
        
        # 3. Creatomate
        print(f"--- Renderizando Video: {d[0]} ---")
        res_v = requests.post("[https://api.creatomate.com/v2/renders](https://api.creatomate.com/v2/renders)", 
            headers={"Authorization": f"Bearer {creatomate_key}"}, 
            json={"template_id": TEMPLATE_ID, "modifications": {"Text-1.text": d[2].upper(), "Text-2.text": d[3]}})
        
        video_url = res_v.json()[0]['url']

        # 4. Guardado final
        sheet.append_row([d[0], link, video_url])
        print(f"🚀 ¡LOGRADO! Producto guardado con éxito.")

    except Exception as e:
        print(f"❌ Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
