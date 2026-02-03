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
    
    ID_HOJA = "1SoKRt6eXTAP3IlhZRElHFv8rejr-qVmMoGsKkO__eZQ"  # <--- COLOCA TU ID AQUÍ
    TAG_ID = "chmbrand-20"    # <--- COLOCA TU TAG AQUÍ

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

        # 3. Pedir los 10 productos a Gemini
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        prompt = """Dame los 10 productos más virales de Amazon/TikTok hoy. 
        Formato: Producto | Hook | Script de 20 palabras | Busqueda Amazon"""
        
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
        respuesta_ia = res.json()['candidates'][0]['content']['parts'][0]['text']
        lineas = respuesta_ia.strip().split('\n')

        for i, linea in enumerate(lineas[:10]):
            if "|" in linea:
                datos = [d.strip() for d in linea.split('|')]
                producto, hook, script, busqueda = datos[0], datos[1], datos[2], datos[3]
                
                link = f"https://www.amazon.com/s?k={busqueda.replace(' ', '+')}&tag={TAG_ID}"
                desc = f"Get yours here: {link} #amazonfinds #viral"
                
                # Guardar en Sheets
                sheet.append_row([producto, hook, script, link, desc])

                # 4. CREACIÓN DEL VIDEO GRATIS (Solo para el primer producto para no saturar GitHub)
                if i == 0:
                    generar_video_archivo(producto, script, i)

        print("🚀 Proceso completado: Datos en Sheets y Video generado.")

    except Exception as e:
        print(f"❌ Error: {e}")

def generar_video_archivo(producto, script, indice):
    try:
        print(f"🎬 Generando video para: {producto}")
        
        # A. Crear Audio (Gratis)
        tts = gTTS(text=script, lang='en')
        audio_path = f"audio_{indice}.mp3"
        tts.save(audio_path)
        audio_clip = AudioFileClip(audio_path)
        duracion = audio_clip.duration

        # B. Crear Fondo Visual (Vertical para TikTok)
        fondo = ColorClip(size=(1080, 1920), color=(30, 30, 30)).set_duration(duracion)

        # C. Texto del Producto
        txt_prod = TextClip(producto, fontsize=80, color='yellow', font='Arial-Bold',
                           size=(900, None), method='caption').set_position(('center', 300)).set_duration(duracion)

        # D. Subtítulos del Script
        txt_script = TextClip(script, fontsize=60, color='white', font='Arial',
                             size=(800, None), method='caption').set_position('center').set_duration(duracion)

        # E. Montaje Final
        video = CompositeVideoClip([fondo, txt_prod, txt_script]).set_audio(audio_clip)
        video.write_videofile(f"video_viral_{indice}.mp4", fps=24, codec="libx264", audio_codec="aac")
        
    except Exception as e:
        print(f"⚠️ No se pudo crear el video: {e}")

if __name__ == "__main__":
    ejecutar_sistema_infinito()
