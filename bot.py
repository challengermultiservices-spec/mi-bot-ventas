import os
import requests
import json
import gspread
from google.oauth2.service_account import Credentials
from gtts import gTTS
from moviepy.editor import TextClip, ColorClip, CompositeVideoClip, AudioFileClip

def ejecutar_sistema_infinito():
    # 1. Configuración de Credenciales
    api_key = os.environ.get("GEMINI_API_KEY")
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    
    # --- CONFIGURACIÓN PERSONAL ---
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"  # Reemplaza con tu ID
    TAG_ID = "chmbrand-20"    # Reemplaza con tu Tag
    # ------------------------------

    if not creds_raw:
        print("❌ Error: No se encontraron credenciales.")
        return

    try:
        # 2. Conexión a Google Sheets
        creds_json = json.loads(creds_raw)
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_json, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(ID_HOJA).get_worksheet(0)

        # 3. Pedir los 10 productos a Gemini con Script detallado
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        prompt = """Analiza los 10 productos más virales hoy. 
        Responde UNA LÍNEA por producto con este formato:
        Producto | Hook | Script de 15 palabras | Termino Busqueda"""
        
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
        respuesta_ia = res.json()['candidates'][0]['content']['parts'][0]['text']
        lineas = [l for l in respuesta_ia.strip().split('\n') if "|" in l]

        for i, linea in enumerate(lineas[:10]):
            datos = [d.strip() for d in linea.split('|')]
            if len(datos) >= 4:
                producto, hook, script, busqueda = datos[0], datos[1], datos[2], datos[3]
                
                link = f"https://www.amazon.com/s?k={busqueda.replace(' ', '+')}&tag={TAG_ID}"
                desc = f"{hook} ✨ Get it here: {link} #amazonfinds #viral"
                
                # Guardar en Google Sheets
                sheet.append_row([producto, hook, script, link, desc])

                # 4. Intentar crear el video para el primer producto
                if i == 0:
                    generar_video_gratis(producto, script, i)

        print("🚀 Proceso terminado con éxito.")

    except Exception as e:
        print(f"❌ Error en el bot: {e}")

def generar_video_gratis(titulo, script, id):
    try:
        print(f"🎬 Renderizando video para: {titulo}")
        
        # Audio con gTTS
        audio_file = f"audio_{id}.mp3"
        tts = gTTS(text=script, lang='en')
        tts.save(audio_file)
        audio = AudioFileClip(audio_file)
        
        # Fondo y Texto
        # Usamos fuentes genéricas como 'DejaVu-Sans' que vienen en Ubuntu/GitHub
        fondo = ColorClip(size=(720, 1280), color=(20, 20, 20)).set_duration(audio.duration)
        
        txt_titulo = TextClip(titulo.upper(), fontsize=50, color='yellow', font='DejaVu-Sans-Bold',
                             method='caption', size=(600, None)).set_position(('center', 200)).set_duration(audio.duration)
        
        txt_script = TextClip(script, fontsize=40, color='white', font='DejaVu-Sans',
                             method='caption', size=(600, None)).set_position('center').set_duration(audio.duration)

        video = CompositeVideoClip([fondo, txt_titulo, txt_script]).set_audio(audio)
        video.write_videofile(f"video_final_{id}.mp4", fps=24, codec="libx264")
        
    except Exception as e:
        print(f"⚠️ Error al crear video: {e}")

if __name__ == "__main__":
    ejecutar_sistema_infinito()
