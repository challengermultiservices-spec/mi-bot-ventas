import asyncio
from playwright.async_api import async_playwright
import google.generativeai as genai
import os

# Configuramos la IA
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

async def buscar_productos():
    async with async_playwright() as p:
        print("Iniciando navegador...")
        browser = await p.chromium.launch(headless=True)
        # Este contexto 'disfraza' al bot de un usuario real
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print("Entrando a Amazon Best Sellers...")
            await page.goto('https://www.amazon.com/gp/bestsellers/kitchen/', wait_until="networkidle")
            
            # Buscamos los productos
            titulos = await page.locator('div[class*="sc-css-line-clamp"]').all_inner_texts()
            
            if not titulos:
                titulos = await page.locator('span div').all_inner_texts()

            lista_texto = "\n".join(titulos[:8])
            print(f"Productos detectados: {len(titulos)}")

            prompt = f"Analiza estos productos tendencia y dime los 2 mejores para TikTok Shop. Dame un Gancho (Hook) para el video: {lista_texto}"
            response = model.generate_content(prompt)
            
            print("\n" + "="*30)
            print("🤖 RESULTADO DE LA IA:")
            print(response.text)
            print("="*30)

        except Exception as e:
            print(f"Hubo un detalle: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(buscar_productos())
