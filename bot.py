import asyncio
import google.generativeai as genai
import os

# Configuración directa
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

async def obtener_tendencias():
    print("Iniciando análisis con Modelo Pro...")
    
    # Probamos con 'gemini-pro', que es la versión de producción más estable
    try:
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = """
        Eres experto en TikTok Shop USA y Dropshipping. 
        Hoy es 2 de febrero de 2026. 
        Dime 3 productos de cocina que son tendencia viral en este momento.
        Dame: Nombre, Hook de video y por qué se vende.
        """
        
        response = model.generate_content(prompt)
        
        print("\n" + "✅" * 10)
        print("RESULTADO FINAL:")
        print(response.text)
        print("✅" * 10)

    except Exception as e:
        print(f"Error con Pro: {e}")
        # Último recurso: intentar con la versión específica 1.0
        print("Intentando último recurso...")
        model_fallback = genai.GenerativeModel('models/gemini-1.0-pro')
        response = model_fallback.generate_content("Dime 2 productos virales de cocina.")
        print(response.text)

if __name__ == "__main__":
    asyncio.run(obtener_tendencias())
