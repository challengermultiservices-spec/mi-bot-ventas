import os, requests, json, gspread, time, random, sys
from google.oauth2.service_account import Credentials

def ejecutar_sistema_automatico():
    gemini_key = os.environ.get("GEMINI_API_KEY")
    creatomate_key = os.environ.get("CREATOMATE_API_KEY")
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    # Ahora que eres PRO, podemos usar categorías más competitivas
    categorias = ["Hogar Inteligente", "Gadgets Tech", "Mascotas", "Cocina Profesional"]
    cat = random.choice(categorias)
    
    # Prioridad ahora es el modelo 1.5-PRO
    modelos = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash"]

    try:
        print(f"--- Iniciando proceso PRO para categoría: {cat} ---")
        creds = Credentials.from_service_account_info(json.loads(creds_raw), scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        sheet = gspread.authorize(creds).open_by_key(ID_HOJA).get_worksheet(0)

        res_g = None
        for m in modelos:
            print(f"--- Solicitando a {m} ---")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={gemini_key}"
            # Prompt más profesional para mejores resultados
            p = {"contents": [{"parts": [{"text": f"Eres un experto en ventas de Amazon. Sugiere un producto viral de {cat}. Responde solo en este formato: NOMBRE | TERMINO DE BUSQUEDA | HOOK IMPACTANTE | SCRIPT CORTO PARA VIDEO"}]}]}
            
            r = requests.post(url, json=p)
            if r.status_code == 200:
                res_g = r.json()
                print(f"✅ Respuesta recibida de {m}")
                break
            else:
                print(f"⚠️ {m} no disponible, probando siguiente...")

        if not res_g:
            print("❌ Error: No se pudo conectar con la API de Gemini.")
            sys.exit(1)

        t = res_g['candidates'][0]['content']['parts'][0]['text']
        d = [x.strip() for x in t.split('|')]
        
        # Crear link de afiliado
        link = f"https://www.amazon.com/s?k={d[1].replace(' ', '+')}&tag={AMAZON_TAG}"

        # Generar Video en Creatomate
        print(f"--- Enviando a Creatomate: {d[0]} ---")
        res_c = requests.post("https://api.creatomate.com/v2/renders", 
            headers={"Authorization": f"Bearer {creatomate_key}"}, 
            json={
                "template_id": TEMPLATE_ID, 
                "modifications": {
                    "Text-1.text": d[2].upper(), 
                    "Text-2.text": d[3]
                }
            })
        
        video_url = res_c.json()[0]['url']

        # Guardar en Sheets (A: Producto, B: Link, C: Video)
        sheet.append_row([d[0], link, video_url])
        print(f"🚀 ¡TODO LISTO! Producto: {d[0]}")

    except Exception as e:
        print(f"❌ Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
