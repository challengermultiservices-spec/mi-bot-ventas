import asyncio
from playwright.async_api import async_playwright
import google.generativeai as genai
import os

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

async def buscar_productos():
    async with async_playwright() as p:
        print("Iniciando navegador...")
        browser = await p.chromium.launch(headless=True)
        # Disfraz avanzado: Simulamos una resolución de pantalla y un navegador real
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # Cambiamos la URL a una búsqueda de productos virales (menos bloqueos)
            print("Buscando productos virales de cocina en Amazon...")
            await page.goto('https://www.amazon.com/s?k=tiktok+kitchen+gadgets', wait_until="domcontentloaded")
            
            # Esperamos a que los productos carguen
            await page.wait_for_selector('h2 span', timeout=15000)
            
            # Extraemos los nombres de los productos
            titulos = await page.locator('h2 span').all_inner_texts()
            
            # Limpiamos la lista (quitamos textos vacíos)
            productos = [t.strip() for t in titulos if len(t) > 10]
            
            print(f"Productos detectados: {len(productos)}")

            if len(productos) > 0:
                lista_texto = "\n".join(productos[:12])
                prompt = f"De esta lista de gadgets de cocina virales, elige los 2 más llamativos para vender en TikTok Shop USA. Para cada uno dame: 1) Nombre corto, 2) Por qué es viral, 3) Un 'Hook' (gancho) de 3 segundos para el video: {lista_texto}"
                
                response = model.generate_content(prompt)
                print("\n" + "⭐" * 20)
                print("🤖 RECOMENDACIÓN DE LA IA:")
                print(response.text)
                print("⭐" * 20)
            else:
                print("Amazon sigue ocultando los datos. Vamos a intentar un método alternativo en el siguiente paso.")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(buscar_productos())
