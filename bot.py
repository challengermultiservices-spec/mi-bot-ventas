import asyncio
import google.generativeai as genai
import os

# 1. Configuración de la IA con el modelo de producción estable
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    # Cambiamos a 'gemini-1.5-flash-latest' para evitar el error 404
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    print("IA Configurada correctamente.")
except Exception as e:
    print(f"Error configurando la IA: {e}")

async def obtener_tendencias():
    print("Analizando tendencias de TikTok Shop USA (Febrero 2026)...")
    
    prompt = """
    Eres un analista experto en TikTok Shop USA. 
    Dime los 3 productos de cocina que son tendencia viral HOY 2 de febrero de 2026.
    Para cada uno entrega:
    - Nombre del producto
    - Por qué es viral
    - Un Hook para el video
    - Recomendación de precio de venta
    """
    
    try:
        # Generar contenido con el modelo actualizado
        response = model.generate_content(prompt)
        print("\n" + "🚀" * 15)
        print("💎 PRODUCTOS GANADORES DE HOY:")
        print(response.text)
        print("🚀" * 15)
    except Exception as e:
        print(f"Error específico: {e}")
        print("Si el error persiste, intentaremos con el modelo 'gemini-pro'.")

if __name__ == "__main__":
    asyncio.run(obtener_tendencias())
