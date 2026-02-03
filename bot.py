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

    categorias = ["Hogar Inteligente", "Gadgets Tech", "Cocina", "Mascotas"]
    cat = random.choice(categorias)

    try:
        # 1. Conexión a Sheets
        print(f"--- Conectando a Google Sheets ---")
        creds_info = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_info, 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        client = gspread.authorize(creds)
        sheet = client.open_by_key(ID_HOJA).get_worksheet(0)
        print("✅ Conexión con Sheets exitosa.")

        # 2. Gemini con Limpieza de Respuesta
        print(f"--- Solicitando producto de {cat} ---")
        modelos_y_versiones = [
            ("v1beta", "gemini-2.0-flash"),
            ("v1beta", "gemini-1.5-pro"),
            ("v1", "gemini-1.5-flash")
        ]

        res_g = None
        for version, modelo in modelos_y_versiones:
            url = f"https://generativelanguage.googleapis.com/{version}/models/{modelo}:generateContent?key={gemini_key}"
            # Prompt reforzado para evitar texto extra
            prompt = f"Producto viral Amazon {cat}. Responde UNICAMENTE con este formato, sin introducciones: NOMBRE | BUSQUEDA | HOOK | SCRIPT"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            
            r = requests.post(url, json=payload)
            res_json = r.json()
            if 'candidates' in res_json:
                res_g = res_json
                print(f"✅ ¡Éxito con {modelo}!")
                break

        if not res_g:
            print("❌ Ningún modelo Gemini respondió."); sys.exit(1)

        # LIMPIEZA CRITICA: Quitamos Markdown y saltos de línea extra
        texto_sucio = res_g['candidates'][0]['content']['parts'][0]['text']
        texto_limpio = texto_sucio.replace('```', '').replace('markdown', '').strip()
        
        # Dividimos y verificamos
        d = [x.strip() for x in texto_limpio.split('|')]
        
        if len(d) < 4:
            print(f"⚠️ Formato incorrecto, intentando reparar...")
            # Si el separador falló, intentamos por líneas si es necesario
            if "\n" in texto_limpio and len(d) < 4:
                d = [x.strip() for x in texto_limpio.split('\n') if x.strip()][:4]

        if len(d) < 4:
            print(f"❌ Imposible procesar respuesta: {texto_limpio}")
            sys.exit(1)

        producto, busqueda, hook, cuerpo = d[0], d[1], d[2], d[3]
        link_afiliado = f"[https://www.amazon.com/s?k=](https://www.amazon.com/s?k=){busqueda.replace(' ', '+')}&tag={AMAZON_TAG}"
        
        # 3. Creatomate
        print(f"--- Renderizando Video: {producto} ---")
        res_v = requests.post("[https://api.creatomate.com/v2/renders](https://api.creatomate.com/v2/renders)", 
            headers={"Authorization": f"Bearer {creatomate_key}"}, 
            json={"template_id": TEMPLATE_ID, "modifications": {"Text-1.text": hook.upper(), "Text-2.text": cuerpo}})
        
        render_data = res_v.json()
        video_url = render_data[0]['url']

        # 4. Guardado final
        sheet.append_row([producto, link_afiliado, video_url])
        print(f"🚀 ¡LOGRADO! {producto} guardado en Google Sheets.")

    except Exception as e:
        print(f"❌ Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
