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
        # Disfraz de navegador real para evitar el Timeout
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print("Entrando a Amazon (con paciencia)...")
            # Quitamos 'networkidle' para que no espere a que cargue toda la publicidad pesada
            await page.goto('https://www.amazon.com/gp/bestsellers/kitchen/', wait_until="domcontentloaded", timeout=60000)
            
            # Esperamos un poco a que aparezcan los productos
            await page.wait_for_timeout(5000) 

            # Buscamos los títulos (ajustado para ser más preciso)
            titulos = await page.locator('div[class*="p13n-sc-truncate"]').all_inner_texts()
            
            if not titulos:
                # Intento alternativo si el primero falla
                titulos = await page.locator('div._cDE39_p13n-sc-css-line-clamp-3_g30T1').all_inner_texts()

            print(f"Productos detectados: {len(titulos)}")
            lista_texto = "\n".join(titulos[:10])

            if len(titulos) > 0:
                prompt = f"Analiza estos productos tendencia y dime los 2 mejores para TikTok Shop. Dame un Gancho (Hook) para el video: {lista_texto}"
                response = model.generate_content(prompt)
                print("\n" + "="*30)
                print("🤖 RESULTADO DE LA IA:")
                print(response.text)
                print("="*30)
            else:
                print("No logré leer los nombres, Amazon nos bloqueó la vista.")

        except Exception as e:
            print(f"Hubo un detalle: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(buscar_productos())
