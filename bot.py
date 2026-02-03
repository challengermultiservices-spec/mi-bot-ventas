import asyncio
from playwright.async_api import async_playwright
import google.generativeai as genai
import os

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

async def buscar_productos():
    async with async_playwright() as p:
        print("Iniciando navegador...")
        # Usamos un 'User Agent' para parecer un humano
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print("Entrando a Amazon...")
            await page.goto('https://www.amazon.com/gp/bestsellers/kitchen/', wait_until="networkidle")
            
            # Buscamos los títulos de los productos
            titulos = await page.locator('div[class*="sc-css-line-clamp"]').all_inner_texts()
            
            if not titulos:
                print("No se encontraron títulos, intentando método alternativo...")
                titulos = await page.locator('span div').all_inner_texts()

            lista_texto = "\n".join(titulos[:8])
            print(f"Productos encontrados: {len(titulos)}")

            prompt = f"Analiza estos productos tendencia en Amazon y dime los 2 mejores para vender en TikTok Shop USA. Dame un 'gancho' (hook) para el video: {lista_texto}"
            response = model.generate_content(prompt)
            
            print("\n--- RECOMENDACIÓN DE GEMINI ---")
            print(response.text)

        except Exception as e:
            print(f"Error durante la ejecución: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(buscar_productos())
