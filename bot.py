import asyncio
from playwright.async_api import async_playwright
import google.generativeai as genai
import os

# Configuramos la IA con la llave que guardaremos en el siguiente paso
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

async def buscar_productos():
    async with async_playwright() as p:
        print("Iniciando búsqueda de productos...")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Entramos a los más vendidos de Amazon (Hogar y Cocina)
        await page.goto('https://www.amazon.com/gp/bestsellers/home-garden/')
        await page.wait_for_timeout(3000)
        
        # Extraemos los nombres de los productos
        titulos = await page.locator('div._cDE39_p13n-sc-css-line-clamp-3_g30T1').all_inner_texts()
        lista_texto = "\n".join(titulos[:10])
        
        # La IA elige los mejores para TikTok
        prompt = f"Analiza estos productos y dime los 2 mejores para TikTok Shop. Explica por qué: {lista_texto}"
        response = model.generate_content(prompt)
        
        print("\n--- ANALISIS DE LA IA ---")
        print(response.text)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(buscar_productos())
