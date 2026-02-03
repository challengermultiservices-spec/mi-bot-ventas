import asyncio
from playwright.async_api import async_playwright
import google.generativeai as genai
import os

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

async def buscar_productos():
    async with async_playwright() as p:
        print("Iniciando navegador sigiloso...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # Usamos eBay Trends / Best Sellers que es más permisivo
            print("Buscando tendencias en productos de cocina...")
            await page.goto('https://www.ebay.com/b/Kitchen-Dining-Bar/20625/bn_1865330', wait_until="domcontentloaded")
            
            # Esperamos a que carguen los nombres de productos
            await page.wait_for_timeout(5000)
            
            # Extraemos títulos de productos (selector genérico de eBay)
            titulos = await page.locator('.s-item__title').all_inner_texts()
            
            # Limpiar ruidos como "New Listing"
            productos = [t.replace("New Listing", "").strip() for t in titulos if len(t) > 15]
            
            print(f"Productos detectados: {len(productos)}")

            if len(productos) > 0:
                lista_texto = "\n".join(productos[:15])
                prompt = f"Basado en estos productos populares en USA, dime los 2 mejores para crear contenido viral en TikTok Shop. Para cada uno dame: 1) Nombre, 2) Gancho de video (Hook), 3) Por qué se venderá bien: {lista_texto}"
                
                response = model.generate_content(prompt)
                print("\n" + "🚀" * 15)
                print("🤖 ANÁLISIS PARA TIKTOK SHOP:")
                print(response.text)
                print("🚀" * 15)
            else:
                print("No se detectaron productos. Intentando última opción...")
                # Si falla, le damos una lista de respaldo a la IA para que no te vayas con las manos vacías
                prompt = "Dame 2 ideas de productos de cocina que son tendencia en TikTok Shop USA ahora mismo y un hook para cada uno."
                response = model.generate_content(prompt)
                print("\n💡 IDEAS DE RESPALDO DE LA IA:\n", response.text)

        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(buscar_productos())
