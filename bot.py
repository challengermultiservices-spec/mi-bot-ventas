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
        # 1. Conexión a Sheets
        print("--- Conectando a Google Sheets ---")
        creds_info = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_info, 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        client = gspread.authorize(creds)
        sheet = client.open_by_key(ID_HOJA).get_worksheet(0)
        print("✅ Conexión con Sheets exitosa.")

        # 2. Gemini
        print(f"--- Solicitando producto de {cat} ---")
        url_gemini = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
        prompt = f"Producto viral Amazon {cat}. Responde UNICAMENTE: NOMBRE | BUSQUEDA | HOOK | SCRIPT"
        
        r = requests.post(url_gemini, json={"contents": [{"parts": [{"text": prompt}]}]})
        res_json = r.json()
        
        texto_sucio = res_json['candidates'][0]['content']['parts'][0]['text']
        texto_limpio = texto_sucio.replace('```', '').replace('markdown', '').strip()
        d = [x.strip() for x in texto_limpio.split('|')]
        
        if len(d) < 4:
            print("❌ Error en formato de respuesta"); sys.exit(1)

        producto, busqueda, hook, cuerpo = d[0], d[1], d[2], d[3]
        link_afiliado = f"[https://www.amazon.com/s?k=](https://www.amazon.com/s?k=){busqueda.replace(' ', '+')}&tag={AMAZON_TAG}"
        
        # 3. Creatomate (URL CORREGIDA SIN FORMATO)
        print(f"--- Renderizando Video: {producto} ---")
        url_creatomate = "[https://api.creatomate.com/v2/renders](https://api.creatomate.com/v2/renders)"
        headers = {
            "Authorization": f"Bearer {creatomate_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "template_id": TEMPLATE_ID,
            "modifications": {
                "Text-1.text": hook.upper(),
                "Text-2.text": cuerpo
            }
        }
        
        res_v = requests.post(url_creatomate, headers=headers, json=payload)
        
        if res_v.status_code not in [200, 201]:
            print(f"❌ Error Creatomate: {res_v.text}"); sys.exit(1)
            
        video_url = res_v.json()[0]['url']

        # 4. Guardado final
        sheet.append_row([producto, link_afiliado, video_url])
        print(f"🚀 ¡EXITO TOTAL! Revisa tu Google Sheets.")

    except Exception as e:
        print(f"❌ Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
