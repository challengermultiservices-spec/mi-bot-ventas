import asyncio
import google.generativeai as genai
import os

# 1. Configuración de la IA
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    # Usamos la versión más estable disponible
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("IA Configurada correctamente.")
except Exception as e:
    print(f"Error configurando la IA: {e}")

async def obtener_tendencias():
    print("Analizando tendencias de TikTok Shop USA (Febrero 2026)...")
    
    # Este prompt le pide a la IA que use su conocimiento en tiempo real 
    # sobre lo que es viral en este momento exacto.
    prompt = """
    Eres un experto en dropshipping para TikTok Shop USA. 
    Dime los 3 productos de cocina más VIRALES hoy, 2 de febrero de 2026.
    Para cada uno entrega:
    - Nombre del producto
    - Por qué es viral hoy
    - Un GANCHO (Hook) de 2 segundos para el video
    - Puntuación de dificultad para vender (1-10)
    """
    
    try:
        response = model.generate_content(prompt)
        print("\n" + "🚀" * 15)
        print("💎 PRODUCTOS GANADORES DE HOY:")
        print(response.text)
        print("🚀" * 15)
    except Exception as e:
        print(f"Error al generar contenido: {e}")
        print("Verifica que tu GEMINI_API_KEY sea correcta en los Secrets de GitHub.")

if __name__ == "__main__":
    asyncio.run(obtener_tendencias())
