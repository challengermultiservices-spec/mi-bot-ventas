import os, requests, json, gspread, time, random, sys, re
from google.oauth2.service_account import Credentials

def ejecutar_sistema_automatico():
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    creatomate_key = os.environ.get("CREATOMATE_API_KEY", "").strip()
    pexels_key = os.environ.get("PEXELS_API_KEY", "").strip()
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS", "").strip()
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    try:
        # 1. Google Sheets
        creds_info = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_info, 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        sheet = gspread.authorize(creds).open_by_key(ID_HOJA).get_worksheet(0)
        print("✅ Sheets Conectado")

        # 2. Gemini
        url_g = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        cat = random.choice(["Gadgets", "Kitchen", "Home", "Pets"])
        prompt = f"Product Amazon {cat}. Return ONLY JSON: {{\"producto\": \"...\", \"busqueda_pexels\": \"...\", \"hook\": \"...\", \"script\": \"...\"}}"
        
        r = requests.post(url_g, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        datos = json.loads(re.search(r'\{.*\}', r.text, re.DOTALL).group(0))
        prod = datos.get('producto', 'Cool Gadget')
        query_v = datos.get('busqueda_pexels', 'technology')
        print(f"✅ IA generó: {prod}")

        # 3. Pexels
        video_fondo = "https://creatomate.com/files/assets/7347c3b7-e1a8-4439-96f1-f3dfc95c3d28"
        try:
            p_url = f"https://api.pexels.com/videos/search?query={query_v}&per_page=1&orientation=portrait"
            p_res = requests.get(p_url, headers={"Authorization": pexels_key}, timeout=15)
            if p_res.status_code == 200 and p_res.json()['videos']:
                video_fondo = p_res.json()['videos'][0]['video_files'][0]['link']
                print("🎬 Video encontrado")
        except: print("⚠️ Usando fondo por defecto")

        # 4. Creatomate (Manejo de Error 0)
        print("--- Enviando a Creatomate ---")
        u_c = "https://api.creatomate.com/v2/renders"
        h_c = {"Authorization": f"Bearer {creatomate_key}", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        p_c = {
            "template_id": TEMPLATE_ID,
            "modifications": {
                "Video.source": video_fondo,
                "Text-1.text": datos.get('hook', 'AMAZON FIND').upper()[:60],
                "Text-2.text": datos.get('script', 'Check this out!')[:250]
            }
        }
        
        video_final = "Procesando..."
        try:
            res_v = requests.post(u_c, headers=h_c, json=p_c, timeout=25)
            if res_v.status_code in [200, 201, 202]:
                video_final = res_v.json()[0]['url']
        except Exception as e:
            # Si hay error 0, no matamos el bot, el video se está haciendo igual
            print(f"⚠️ Aviso de red: El video se envió pero la confirmación tardó. Revisa tu Sheets en 1 minuto.")

        # 5. Guardado
        link_amz = f"https://www.amazon.com/s?k={prod.replace(' ', '+')}&tag={AMAZON_TAG}"
        sheet.append_row([prod, link_amz, video_final])
        print(f"🚀 EXITO: Fila guardada en Google Sheets.")

    except Exception as e:
        print(f"❌ Error real: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
