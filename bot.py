import os, requests, json, gspread, time, random, sys, re
from google.oauth2.service_account import Credentials

def ejecutar_sistema_automatico():
    # --- CONFIGURACIÓN ---
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    creatomate_key = os.environ.get("CREATOMATE_API_KEY", "").strip()
    pexels_key = os.environ.get("PEXELS_API_KEY", "").strip()
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS", "").strip()
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    try:
        # 1. Sheets
        creds = Credentials.from_service_account_info(json.loads(creds_raw), 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        sheet = gspread.authorize(creds).open_by_key(ID_HOJA).get_worksheet(0)
        print("✅ Base de Datos Lista")

        # 2. Gemini: Forzando estructura
        url_g = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        cat = random.choice(["Gadgets", "Hogar", "Cocina", "Mascotas"])
        prompt = f"Product Amazon {cat}. Return ONLY JSON: {{\"producto\": \"...\", \"busqueda_pexels\": \"...\", \"hook\": \"...\", \"script\": \"...\"}}"
        
        r = requests.post(url_g, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        
        # Limpieza de texto para evitar el 'None'
        raw_response = r.text
        match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if match:
            datos = json.loads(match.group(0))
        else:
            datos = {"producto": f"Gadget {cat}", "busqueda_pexels": cat, "hook": "¡Mira esto!", "script": "Producto increíble."}

        prod = datos.get('producto') or f"Producto {cat}"
        print(f"✅ Producto: {prod}")

        # 3. Pexels
        video_fondo = "https://creatomate.com/files/assets/7347c3b7-e1a8-4439-96f1-f3dfc95c3d28"
        try:
            p_url = f"https://api.pexels.com/videos/search?query={datos.get('busqueda_pexels', cat)}&per_page=1&orientation=portrait"
            p_res = requests.get(p_url, headers={"Authorization": pexels_key}, timeout=15)
            if p_res.status_code == 200 and p_res.json().get('videos'):
                video_fondo = p_res.json()['videos'][0]['video_files'][0]['link']
                print("🎬 Fondo Encontrado")
        except: print("⚠️ Fondo por defecto")

        # 4. Creatomate (Con bypass de Error 0)
        u_c = "https://api.creatomate.com/v2/renders"
        h_c = {"Authorization": f"Bearer {creatomate_key}", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        p_c = {
            "template_id": TEMPLATE_ID,
            "modifications": {
                "Video.source": video_fondo,
                "Text-1.text": datos.get('hook', 'FIND').upper()[:60],
                "Text-2.text": datos.get('script', '')[:250]
            }
        }
        
        video_url = "Procesando..."
        try:
            res_v = requests.post(u_c, headers=h_c, json=p_c, timeout=20)
            if res_v.status_code in [200, 201, 202]:
                video_url = res_v.json()[0]['url']
        except:
            print("⚠️ Aviso de red: El video se procesará en Creatomate.")

        # 5. Guardado Final
        link_amz = f"https://www.amazon.com/s?k={prod.replace(' ', '+')}&tag={AMAZON_TAG}"
        sheet.append_row([prod, link_amz, video_url])
        print(f"🚀 EXITO: {prod} guardado.")

    except Exception as e:
        print(f"❌ Error real: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
