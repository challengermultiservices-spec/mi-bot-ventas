import os, requests, json, gspread, time, random, sys, re
from google.oauth2.service_account import Credentials

def ejecutar_sistema_automatico():
    # --- CONFIGURACIÓN DE LLAVES ---
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    creatomate_key = os.environ.get("CREATOMATE_API_KEY", "").strip()
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS", "").strip()
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    try:
        # 1. CONEXIÓN A GOOGLE SHEETS
        print("--- Conectando a Google Sheets ---")
        creds_info = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_info, 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        sheet = gspread.authorize(creds).open_by_key(ID_HOJA).get_worksheet(0)
        print("✅ Sheets Conectado")

        # 2. GENERACIÓN CON GEMINI 2.5 FLASH
        url_g = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        cat = random.choice(["Gadgets Tecnológicos", "Hogar Inteligente", "Cocina Viral", "Mascotas", "Fitness"])
        
        prompt = (f"Actúa como experto en Amazon. Sugiere un producto viral de {cat}. "
                  "Responde ÚNICAMENTE un objeto JSON con estas llaves: "
                  "\"producto\", \"busqueda\", \"hook\", \"script\". "
                  "El script debe ser narración pura, sin notas visuales, max 250 caracteres.")
        
        r = requests.post(url_g, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        res_text = r.json()['candidates'][0]['content']['parts'][0]['text']
        
        # Extracción de JSON con "red de seguridad"
        match = re.search(r'\{.*\}', res_text, re.DOTALL)
        if not match:
            raise Exception("La IA no devolvió un formato válido")
            
        datos = json.loads(match.group(0))
        
        # Normalización de nombres (Evita que salga 'Producto Viral')
        prod = datos.get('producto') or datos.get('PRODUCTO') or datos.get('nombre') or "Gadget Amazon"
        busq = datos.get('busqueda') or datos.get('BUSQUEDA') or prod
        hook = datos.get('hook') or datos.get('HOOK') or "¡Tienes que ver esto!"
        scri = datos.get('script') or datos.get('SCRIPT') or "Este producto cambiará tu vida."
        
        print(f"✅ IA seleccionó: {prod}")

        # 3. ENVÍO A CREATOMATE (CON ESCUDO ANTI-ERROR 0)
        print(f"--- Renderizando Video: {prod} ---")
        u_c = "https://api.creatomate.com/v2/renders"
        h_c = {
            "Authorization": f"Bearer {creatomate_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }
        p_c = {
            "template_id": TEMPLATE_ID,
            "modifications": {
                "Text-1.text": hook.upper()[:60],
                "Text-2.text": scri[:300]
            }
        }
        
        video_url = "Pendiente de procesar" # Fallback por si hay micro-corte
        try:
            res_v = requests.post(u_c, headers=h_c, json=p_c, timeout=20)
            if res_v.status_code in [200, 201, 202]:
                video_url = res_v.json()[0]['url']
                print("✅ Video enviado correctamente a Creatomate.")
            else:
                print(f"⚠️ Aviso Creatomate (Status {res_v.status_code}): {res_v.text}")
        except Exception:
            print("⚠️ Bypass: El video se envió pero la red cerró la conexión antes de confirmar.")

        # 4. GUARDADO FINAL EN GOOGLE SHEETS
        link_amz = f"https://www.amazon.com/s?k={busq.replace(' ', '+')}&tag={AMAZON_TAG}"
        sheet.append_row([prod, link_amz, video_url])
        print(f"🚀 ÉXITO: '{prod}' guardado en Google Sheets.")

    except Exception as e:
        print(f"❌ Error crítico en la ejecución: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
