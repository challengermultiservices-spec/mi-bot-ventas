import os, requests, json, gspread, time, random, sys, re
from google.oauth2.service_account import Credentials

def ejecutar_sistema_automatico():
    gemini_key = os.environ.get("GEMINI_API_KEY")
    creatomate_key = os.environ.get("CREATOMATE_API_KEY")
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"
    AMAZON_TAG = "chmbrand-20" 
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"

    cat = random.choice(["Cocina", "Gadgets", "Hogar", "Mascotas"])

    try:
        # 1. Conexión a Sheets
        creds_info = json.loads(creds_raw)
        creds = Credentials.from_service_account_info(creds_info, 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        sheet = gspread.authorize(creds).open_by_key(ID_HOJA).get_worksheet(0)
        print("✅ Sheets Conectado")

        # 2. Gemini 2.5 Flash - Extracción Inteligente
        url_g = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        prompt = f"Producto Amazon viral {cat}. Responde en este formato:\nPRODUCTO: nombre\nBUSQUEDA: terminos\nHOOK: frase corta\nSCRIPT: guion corto narrado"
        
        r = requests.post(url_g, json={"contents": [{"parts": [{"text": prompt}]}]})
        texto = r.json()['candidates'][0]['content']['parts'][0]['text'].replace('**', '')
        
        # Extracción mejorada para guiones largos
        datos = {"PRODUCTO": "", "BUSQUEDA": "", "HOOK": "", "SCRIPT": ""}
        lineas = texto.split('\n')
        
        en_script = False
        script_parts = []

        for linea in lineas:
            linea_u = linea.upper()
            if "PRODUCTO:" in linea_u: datos["PRODUCTO"] = linea.split(':', 1)[-1].strip()
            elif "BUSQUEDA:" in linea_u: datos["BUSQUEDA"] = linea.split(':', 1)[-1].strip()
            elif "HOOK:" in linea_u: datos["HOOK"] = linea.split(':', 1)[-1].strip()
            elif "SCRIPT:" in linea_u: 
                en_script = True
                script_parts.append(linea.split(':', 1)[-1].strip())
            elif en_script:
                script_parts.append(linea.strip())

        # Unimos el script y limpiamos notas visuales (Texto entre paréntesis o con "VOZ EN OFF:")
        script_completo = " ".join(script_parts)
        script_limpio = re.sub(r'\(.*?\)', '', script_completo) # Borra (0-3 seg), (VISUAL:...), etc.
        script_limpio = script_limpio.replace("VOZ EN OFF:", "").replace("Narrador:", "").strip()
        datos["SCRIPT"] = script_limpio[:1000] # Limite para evitar errores de renderizado largo

        if not datos["PRODUCTO"] or not datos["SCRIPT"]:
            print(f"❌ Error de contenido. Datos extraídos: {datos}")
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
        print(f"🚀 ¡LOGRADO! {datos['PRODUCTO']} guardado con éxito.")

    except Exception as e:
        print(f"❌ Error Crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_sistema_automatico()
