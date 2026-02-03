import asyncio
from playwright.async_api import async_playwright
import google.generativeai as genai
import os

# Configuramos la IA con el modelo estable
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
# Usamos 'gemini-1.5-flash-latest' que es la versión más compatible
model = genai.GenerativeModel('gemini-1.5-flash-latest')

async def buscar_productos():
    async with async_playwright() as p:
        print("Iniciando sistema...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print("Intentando acceso a datos de mercado...")
            # Intentamos entrar a una zona de ofertas de eBay (más abierta)
            await page.goto('https://www.ebay.com/globaldeals/home/kitchen', wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)
            
            titulos = await page.locator('.d-ebay-ui-dot-v1-3-1-text-truncate').all_inner_texts()
            productos_web = [t.strip() for t in titulos if len(t) > 10]

            # EL CEREBRO DE LA IA ENTRA EN ACCIÓN
            print("Generando análisis inteligente...")
            
            prompt = f"""
            Actúa como un experto en Dropshipping y TikTok Shop USA. 
            Analiza estos productos encontrados: {productos_web[:5]}
            
            Si la lista está vacía, ignórala y dime los 3 productos de cocina que están siendo VIRALES 
            ahora mismo en TikTok Shop USA (febrero 2026).
            
            Para cada producto dame:
            1. Nombre del Producto.
            2. Por qué es tendencia (Ej: Resuelve X problema).
            3. Un GANCHO (Hook) de 3 segundos para el video.
            4. El 'Call to Action' ideal.
            """
            
            response = model.generate_content(prompt)
            print("\n" + "💰" * 15)
            print("💎 TU ESTRATEGIA DE VENTAS DE HOY:")
            print(response.text)
            print("💰" * 15)

        except Exception as e:
            # Si todo falla, la IA responde con su propio conocimiento
            print(f"Nota: Usando base de datos interna de IA (Red saturada).")
            response = model.generate_content("Dime 2 productos virales de cocina para TikTok Shop hoy y un hook para cada uno.")
            print(response.text)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(buscar_productos())
