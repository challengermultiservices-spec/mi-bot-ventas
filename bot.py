import os
import requests
import json
import gspread
from google.oauth2.service_account import Credentials

def ejecutar_sistema_infinito():
    api_key = os.environ.get("GEMINI_API_KEY")
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ" # Tu ID
    TAG_ID = "chmbrand-20" 

    try:
        creds_json = json.loads(creds_raw)
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_json, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(ID_HOJA).get_worksheet(0)

        # Prompt para Gemini optimizado para InVideo AI
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        cuerpo_prompt = """Actúa como un experto en Dropshipping. Dame los 10 productos más virales hoy.
        Para cada producto, genera UNA SOLA LÍNEA con este formato exacto:
        Nombre | Link Busqueda | Master Prompt InVideo"""

        instrucciones_invideo = """El Master Prompt debe ser un párrafo para InVideo AI que diga: 
        'Crea un video de TikTok de 30 segundos sobre [PRODUCTO]. Usa una voz de hombre joven con acento latino, 
        enérgica y convincente. El guion debe tener un hook impactante, mostrar los beneficios y terminar 
        con un llamado a la acción. Usa clips de alta calidad de stock y música movida.'"""

        payload = {
            "contents": [{"parts": [{"text": f"{cuerpo_prompt} {instrucciones_invideo}"}]}]
        }

        res = requests.post(url, json=payload)
        lineas = res.json()['candidates'][0]['content']['parts'][0]['text'].strip().split('\n')

        for linea in lineas:
            if "|" in linea:
                datos = [d.strip() for d in linea.split('|')]
                if len(datos) >= 3:
                    producto, busqueda, master_prompt = datos[0], datos[1], datos[2]
                    link = f"https://www.amazon.com/s?k={busqueda.replace(' ', '+')}&tag={TAG_ID}"
                    
                    # Guardamos en la columna U (o donde prefieras) para mantener el orden
                    sheet.append_row([producto, link, master_prompt])

        print("🚀 ¡Scripts para InVideo listos en tu Google Sheets!")
        
        except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    ejecutar_sistema_infinito()
