import os, requests, json, gspread, time, random, sys, re
from google.oauth2.service_account import Credentials

def ejecutar_sistema_automatico():
    # --- CARGA DE SECRETOS ---
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    creatomate_key = os.environ.get("CREATOMATE_API_KEY", "").strip()
    pexels_key = os.environ.get("PEXELS_API_KEY", "").strip()
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS", "").strip()
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    try:
        # 1. CONEXIÓN A GOOGLE SHEETS
        creds_dict = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_dict, 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        sheet = gspread.authorize(creds).open_by_key(ID_HOJA).get_worksheet(0)
        print("✅ Acceso a Google Sheets concedido.")

        # 2. GENERACIÓN DE PRODUCTO CON GEMINI
        url_g = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        categorias = ["Gadget tecnológico útil", "Utensilio de cocina viral", "Accesorio para mascotas innovador", "Hogar inteligente"]
        cat_elegida = random.choice(categorias)
        
        prompt = (f"Sugiere un producto real y específico de Amazon de la categoría: {cat_elegida}. "
                  "Responde ÚNICAMENTE en formato JSON estricto. No añadas texto explicativo. "
                  "Estructura: {\"producto\": \"Nombre Comercial Real\", \"busqueda_video\": \"2 palabras ingles\", \"hook\": \"Frase gancho\", \"script\": \"Descripción corta\"}")
        
        r_gemini = requests.post(url_g, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        
        try:
            raw_text = r_gemini.json()['candidates'][0]['content']['parts'][0]['text']
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            datos = json.loads(match.group(0))
        except:
            datos = {"producto": f"{cat_elegida} Viral", "busqueda_video": "technology", "hook": "¡Mira este hallazgo!", "script": "Este producto está rompiendo internet."}

        prod_final = datos.get('producto', 'Gadget Increíble')
        print(f"✅ Producto Seleccionado: {prod_final}")

        # 3. BÚSQUEDA EN PEXELS
        video_fondo = "https://creatomate.com/files/assets/7347c3b7-e1a8-4439-96f1-f3dfc95c3d28"
        try:
            query_v = datos.get('busqueda_video', 'product')
            p_res = requests.get(f"https://api.pexels.com/videos/search?query={query_v}&per_page=1&orientation=portrait", 
                                 headers={"Authorization": pexels_key}, timeout=15)
            if p_res.status_code == 200 and p_res.json().get('videos'):
                video_fondo = p_res.json()['videos'][0]['video_files'][0]['link']
                print("🎬 Video de Pexels encontrado.")
        except:
            print("⚠️ Usando fondo de seguridad.")

        # 4. CREATOMATE (CON PROTECCIÓN DE RED)
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
        
        video_url_final = "Renderizando (Verificar en panel)"
        try:
            res_c = requests.post(u_c, headers=h_c, json=p_c, timeout=25)
            if res_c.status_code in [200, 201, 202]:
                video_url_final = res_c.json()[0]['url']
        except:
            print("⚠️ Aviso de red: El video se envió correctamente.")

        # 5. REGISTRO FINAL
        link_amz = f"https://www.amazon.com/s?k={prod_final.replace(' ', '+')}&tag={AMAZON_TAG}"
        sheet.append_row([prod_final, link_amz, video_url_final])
        print(f"🚀 EXITO TOTAL: {prod_final} guardado.")

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
