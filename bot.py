import google.generativeai as genai
import os

# Configuración ultra-directa
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

def ejecutar():
    print("Conectando con el cerebro de Google...")
    try:
        # Probamos el modelo pro que es el más estable
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content("Dime 2 productos virales para TikTok Shop y un hook.")
        
        print("\n--- ¡EXITO! ---")
        print(response.text)
        print("---------------")
    except Exception as e:
        print(f"Error fatal: {e}")

if __name__ == "__main__":
    ejecutar()
