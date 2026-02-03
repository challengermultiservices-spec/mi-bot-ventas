import os, requests, json, gspread, time, random, sys, re
from google.oauth2.service_account import Credentials

def ejecutar_sistema_automatico():
    gemini_key = os.environ.get("GEMINI_API_KEY")
    creatomate_key = os.environ.get("CREATOMATE_API_KEY")
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    cat = random.choice(["Gadgets", "Hogar Inteligente", "Cocina Pro", "Mascotas", "Gaming"])

    try:
        # 1. Conexión
        creds_info = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_info, 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        sheet = gspread.authorize(creds).open_by_key(ID_HOJA).get_worksheet(0)
        print("✅ Base de Datos Conectada")

        # 2. Generación de Contenido
        url_g = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        prompt = (f"Sugiere un producto viral de {cat}. Responde SOLO un JSON con llaves: "
                  "\"producto\", \"busqueda\", \"hook\", \"script\". Script máximo 250 caracteres.")
        
        r = requests.post(url_g, json={"contents": [{"parts": [{"text": prompt}]}]})
        res_text = r.json()['candidates'][0]['content']['parts'][0]['text']
        datos = json.loads(re.search(r'\{.*\}', res_text, re.DOTALL).group(0))
        print(f"✅ IA generó: {datos['producto']}")

        # 3. Producción de Video con "Pausa de Renderizado"
        print(f"--- Iniciando Producción en Creatomate ---")
        u_c = "https://api.creatomate.com/v2/renders"
        h_c = {"Authorization": f"Bearer {creatomate_key}", "Content-Type": "application/json"}
        payload_v = {
            "template_id": TEMPLATE_ID,
            "modifications": {
                "Text-1.text": datos['hook'].upper()[:60],
                "Text-2.text": datos['script'][:300]
            }
        }
        
        res_v = requests.post(u_c, headers=h_c, json=payload_v)
        res_data = res_v.json()[0]
        
        video_url = res_data['url']
        status = res_data.get('status')

        # Si el video se está procesando (Status 202/planned), esperamos
        if status in ["planned", "waiting", "rendering"]:
            print("⏳ Video en horno (renderizando)... Esperando 15 segundos...")
            time.sleep(15)

        # 4. Guardado Final
        link = f"https://www.amazon.com/s?k={datos['busqueda'].replace(' ', '+')}&tag={AMAZON_TAG}"
        sheet.append_row([datos['producto'], link, video_url])
        print(f"🚀 ¡MISIÓN CUMPLIDA! Revisa tu Excel: {datos['producto']}")

    except Exception as e:
        print(f"❌ Error en el sistema: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
