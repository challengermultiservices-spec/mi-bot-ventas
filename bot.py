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

        # 2. Gemini 2.5 Flash - Extracción por palabras clave
        url_g = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        prompt = f"Producto viral Amazon {cat}. Responde con este formato exacto:\nPRODUCTO: nombre\nBUSQUEDA: terminos\nHOOK: frase corta\nSCRIPT: guion corto"
        
        r = requests.post(url_g, json={"contents": [{"parts": [{"text": prompt}]}]})
        texto = r.json()['candidates'][0]['content']['parts'][0]['text'].replace('**', '')
        
        # Diccionario para extraer datos
        datos = {"PRODUCTO": "", "BUSQUEDA": "", "HOOK": "", "SCRIPT": ""}
        for linea in texto.split('\n'):
            for clave in datos.keys():
                if clave in linea.upper():
                    datos[clave] = linea.split(':', 1)[-1].strip()

        # Validación de seguridad
        if not datos["PRODUCTO"] or not datos["SCRIPT"]:
            print(f"❌ Error de contenido. Recibido: {texto}")
            sys.exit(1)

        link = f"https://www.amazon.com/s?k={datos['BUSQUEDA'].replace(' ', '+')}&tag={AMAZON_TAG}"

        # 3. Creatomate
        print(f"--- Renderizando: {datos['PRODUCTO']} ---")
        u_c = "https://api.creatomate.com/v2/renders"
        h_c = {"Authorization": f"Bearer {creatomate_key}", "Content-Type": "application/json"}
        p_c = {
            "template_id": TEMPLATE_ID,
            "modifications": {
                "Text-1.text": datos["HOOK"].upper(),
                "Text-2.text": datos["SCRIPT"]
            }
        }
        
        res_v = requests.post(u_c, headers=h_c, json=p_c)
        res_data = res_v.json()
        
        if not res_data or 'url' not in res_data[0]:
            print(f"❌ Error Creatomate API: {res_data}")
            sys.exit(1)
            
        v_url = res_data[0]['url']

        # 4. Guardado
        sheet.append_row([datos['PRODUCTO'], link, v_url])
        print(f"🚀 ¡LOGRADO! {datos['PRODUCTO']} guardado.")

    except Exception as e:
        print(f"❌ Error Crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
