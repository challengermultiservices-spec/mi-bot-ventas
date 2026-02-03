import os, requests, json, gspread, time, random, sys, re
from google.oauth2.service_account import Credentials

def ejecutar_sistema_automatico():
    # --- CONFIGURACIÓN DE LLAVES ---
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    creatomate_key = os.environ.get("CREATOMATE_API_KEY", "").strip()
    pexels_key = os.environ.get("PEXELS_API_KEY", "").strip()
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS", "").strip()
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    try:
        # 1. CONEXIÓN A GOOGLE SHEETS
        creds_info = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_info, 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        sheet = gspread.authorize(creds).open_by_key(ID_HOJA).get_worksheet(0)
        print("✅ Sheets Conectado")

        # 2. GEMINI: GENERACIÓN DE PRODUCTO Y BÚSQUEDA
        url_g = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        cat = random.choice(["Gadgets", "Kitchen", "Home", "Pets", "Smart Technology"])
        
        prompt = (f"Product Amazon {cat}. Return ONLY a JSON object with: "
                  "\"producto\", \"busqueda_pexels\", \"hook\", \"script\". "
                  "In 'busqueda_pexels' use 2 English keywords for video stock.")
        
        r = requests.post(url_g, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        datos = json.loads(re.search(r'\{.*\}', r.text, re.DOTALL).group(0))
        
        prod = datos.get('producto', 'Cool Gadget')
        query_video = datos.get('busqueda_pexels', 'technology')
        print(f"✅ IA generó: {prod} (Buscando video para: {query_video})")

        # 3. PEXELS: BUSCAR VIDEO DE FONDO
        video_url_fondo = "https://creatomate.com/files/assets/7347c3b7-e1a8-4439-96f1-f3dfc95c3d28" # Default
        print(f"--- Buscando en Pexels ---")
        try:
            p_url = f"https://api.pexels.com/videos/search?query={query_video}&per_page=1&orientation=portrait"
            p_res = requests.get(p_url, headers={"Authorization": pexels_key}, timeout=15)
            if p_res.status_code == 200 and p_res.json()['videos']:
                # Extraemos el link del video en alta calidad
                video_url_fondo = p_res.json()['videos'][0]['video_files'][0]['link']
                print("🎬 Video encontrado en Pexels")
        except Exception as e:
            print(f"⚠️ Pexels falló, usando fondo por defecto: {e}")

        # 4. CREATOMATE: RENDERIZADO FINAL
        print(f"--- Renderizando en Creatomate ---")
        u_c = "https://api.creatomate.com/v2/renders"
        h_c = {"Authorization": f"Bearer {creatomate_key}", "Content-Type": "application/json"}
        p_c = {
            "template_id": TEMPLATE_ID,
            "modifications": {
                "Video.source": video_url_fondo,
                "Text-1.text": datos.get('hook', 'AMAZON FIND').upper()[:60],
                "Text-2.text": datos.get('script', 'Check this out!')[:250]
            }
        }
        
        res_v = requests.post(u_c, headers=h_c, json=p_c, timeout=30)
        video_final = "Error de render"
        if res_v.status_code in [200, 201, 202]:
            video_final = res_v.json()[0]['url']

        # 5. GUARDADO EN SHEETS
        link_amz = f"https://www.amazon.com/s?k={prod.replace(' ', '+')}&tag={AMAZON_TAG}"
        sheet.append_row([prod, link_amz, video_final])
        print(f"🚀 TODO LISTO: {prod} en tu Sheets.")

    except Exception as e:
        print(f"❌ Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
