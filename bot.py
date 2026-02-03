import os, requests, json, gspread, time, random, sys
from google.oauth2.service_account import Credentials

def ejecutar_sistema_automatico():
    gemini_key = os.environ.get("GEMINI_API_KEY")
    creatomate_key = os.environ.get("CREATOMATE_API_KEY")
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    cat = random.choice(["Gadgets", "Hogar", "Cocina", "Mascotas"])

    try:
        # 1. Conexión a Sheets
        creds_info = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_info, 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        sheet = gspread.authorize(creds).open_by_key(ID_HOJA).get_worksheet(0)
        print("✅ Sheets Conectado")

        # 2. Gemini 2.5 Flash - Extracción Robusta
        url_g = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        prompt = f"Producto viral Amazon {cat}. Responde estrictamente con este formato: NOMBRE | BUSQUEDA | HOOK | SCRIPT"
        
        r = requests.post(url_g, json={"contents": [{"parts": [{"text": prompt}]}]})
        texto_raw = r.json()['candidates'][0]['content']['parts'][0]['text']
        
        # LIMPIEZA TOTAL: Quitamos asteriscos, títulos y etiquetas
        limpio = texto_raw.replace('**', '').replace('NOMBRE:', '').replace('BUSQUEDA:', '').replace('HOOK:', '').replace('SCRIPT:', '').strip()
        
        # Intentamos dividir por '|' o por saltos de línea si falló el anterior
        if '|' in limpio:
            partes = [p.strip() for p in limpio.split('|')]
        else:
            partes = [p.strip() for p in limpio.split('\n') if p.strip()]

        if len(partes) < 4:
            print(f"❌ Error de parsing. Texto recibido: {limpio}")
            sys.exit(1)

        producto, busqueda, hook, cuerpo = partes[0], partes[1], partes[2], partes[3]
        link = f"https://www.amazon.com/s?k={busqueda.replace(' ', '+')}&tag={AMAZON_TAG}"

        # 3. Creatomate - URL Limpia
        print(f"--- Renderizando: {producto} ---")
        u_c = "https://api.creatomate.com/v2/renders"
        h_c = {"Authorization": f"Bearer {creatomate_key}", "Content-Type": "application/json"}
        p_c = {
            "template_id": TEMPLATE_ID,
            "modifications": {
                "Text-1.text": hook.upper(),
                "Text-2.text": cuerpo
            }
        }
        
        res_v = requests.post(u_c, headers=h_c, json=p_c)
        v_url = res_v.json()[0]['url']

        # 4. Guardado
        sheet.append_row([producto, link, v_url])
        print(f"🚀 ÉXITO TOTAL: {producto}")

    except Exception as e:
        print(f"❌ Error Crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
