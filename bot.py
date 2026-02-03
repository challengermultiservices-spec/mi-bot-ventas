import os, requests, json, gspread, time, random, sys
from google.oauth2.service_account import Credentials

def ejecutar_sistema_automatico():
    gemini_key = os.environ.get("GEMINI_API_KEY")
    creatomate_key = os.environ.get("CREATOMATE_API_KEY")
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    categorias = ["Cocina", "Gadgets Tech", "Hogar", "Mascotas"]
    cat = random.choice(categorias)

    try:
        print(f"--- Autenticando en Google Sheets ---")
        info_credenciales = json.loads(creds_raw)
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        
        # Nueva forma de autenticación más robusta
        creds = Credentials.from_service_account_info(info_credenciales, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(ID_HOJA).get_worksheet(0)
        print("✅ Conexión con Sheets exitosa.")

        # --- Gemini ---
        print(f"--- Solicitando producto de {cat} a Gemini Pro ---")
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent?key={gemini_key}"
        payload = {"contents": [{"parts": [{"text": f"Producto viral Amazon {cat}. Responde: NOMBRE | BUSQUEDA | HOOK | SCRIPT"}]}]}
        
        r = requests.post(url, json=payload)
        res_json = r.json()

        if 'candidates' not in res_json:
            print(f"❌ Error en Gemini: {res_json}")
            sys.exit(1)

        t = res_json['candidates'][0]['content']['parts'][0]['text'].replace('```', '').strip()
        d = [x.strip() for x in t.split('|')]
        
        link = f"[https://www.amazon.com/s?k=](https://www.amazon.com/s?k=){d[1].replace(' ', '+')}&tag={AMAZON_TAG}"
        
        # --- Creatomate ---
        print(f"--- Renderizando Video: {d[0]} ---")
        res_c = requests.post("[https://api.creatomate.com/v2/renders](https://api.creatomate.com/v2/renders)", 
            headers={"Authorization": f"Bearer {creatomate_key}"}, 
            json={"template_id": TEMPLATE_ID, "modifications": {"Text-1.text": d[2].upper(), "Text-2.text": d[3]}})
        
        video_url = res_c.json()[0]['url']

        # --- Guardado ---
        sheet.append_row([d[0], link, video_url])
        print(f"🚀 ¡LOGRADO! Fila añadida para {d[0]}.")

    except Exception as e:
        print(f"❌ Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
