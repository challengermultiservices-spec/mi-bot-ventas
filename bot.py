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
    ID_HOJA = "TU_ID_AQUÍ"  # Reemplaza con tu ID de Google Sheets
    TAG_ID = "tu_tag-20"    # Reemplaza con tu Tag de Amazon
    # ------------------------------

    if not creds_raw:
        print("❌ Error: No se encontraron credenciales en Secrets.")
        return

    try:
        # 2. Conexión a Google Sheets
        creds_json = json.loads(creds_raw)
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_json, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(ID_HOJA).get_worksheet(0)
        print(f"✅ Conectado a Sheets: {ID_HOJA}")

        # 3. Pedir los 10 productos a Gemini
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        prompt = """Analiza los 10 productos más virales hoy en TikTok Shop y Amazon USA. 
        Responde estrictamente UNA LÍNEA por producto con este formato:
        Nombre del Producto | Hook | Script de 15 palabras | Termino Busqueda Amazon"""
        
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
        
        if res.status_code != 200:
            print(f"❌ Error API Gemini: {res.text}")
            return

        respuesta_ia = res.json()['candidates'][0]['content']['parts'][0]['text']
        lineas = [l for l in respuesta_ia.strip().split('\n') if "|" in l]

        contador_exito = 0
        for linea in lineas:
            # Limpiamos símbolos que Gemini suele añadir
            datos = [d.strip().replace('*', '').replace('#', '') for d in linea.split('|')]
            
            if len(datos) >= 4 and contador_exito < 10:
                producto, hook, script, busqueda = datos[0], datos[1], datos[2], datos[3]
                
                link = f"https://www.amazon.com/s?k={busqueda.replace(' ', '+')}&tag={TAG_ID}"
                desc = f"{hook} ✨ Get it here: {link} #amazonfinds #viral #tiktokmademebuyit"
                
                # Guardar en Google Sheets
                sheet.append_row([producto, hook, script, link, desc])

                # 4. Generamos el video solo para el primero para evitar saturar el servidor
                if contador_exito == 0:
                    try:
                        generar_video_gratis(producto, script, contador_exito)
                    except Exception as e_video:
                        print(f"⚠️ Error al crear video: {e_video}")
                
                contador_exito += 1

        print(f"🚀 ¡Éxito! {contador_exito} productos guardados en Sheets.")

    except Exception as e:
        print(f"❌ Error General: {e}")

def generar_video_gratis(titulo, script, id):
    print(f"🎬 Iniciando renderizado de video: {titulo}")
    
    # A. Crear Audio con gTTS (Voz de Google)
    audio_file = f"audio_{id}.mp3"
    tts = gTTS(text=script, lang='en')
    tts.save(audio_file)
    audio = AudioFileClip(audio_file)
    
    # B. Crear Fondo Estético (Vertical 9:16)
    duracion = audio.duration
    fondo = ColorClip(size=(720, 1280), color=(15, 15, 15)).set_duration(duracion)
    
    # C. Texto del Título (Usando DejaVu-Sans que es estándar en Linux)
    txt_titulo = TextClip(
        titulo.upper(), 
        fontsize=55, 
        color='yellow', 
        font='DejaVu-Sans-Bold',
        method='caption', 
        size=(600, None)
    ).set_position(('center', 250)).set_duration(duracion)
    
    # D. Texto del Script (Subtítulos dinámicos)
    txt_script = TextClip(
        script, 
        fontsize=45, 
        color='white', 
        font='DejaVu-Sans',
        method='caption', 
        size=(650, None)
    ).set_position('center').set_duration(duracion)

    # E. Composición y Exportación
    video = CompositeVideoClip([fondo, txt_titulo, txt_script]).set_audio(audio)
    video.write_videofile(f"video_viral_{id}.mp4", fps=24, codec="libx264", audio_codec="aac")
    print(f"✅ Video video_viral_{id}.mp4 generado con éxito.")

if __name__ == "__main__":
    ejecutar_sistema_infinito()
