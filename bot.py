import google.generativeai as genai
import os

# Configuramos la llave
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def ejecutar():
    print("Iniciando conexión forzada con el modelo estable...")
    try:
        # Usamos la ruta completa del sistema para que no haya pérdida
        # 'models/gemini-1.0-pro' es el modelo más compatible que existe
        model = genai.GenerativeModel('models/gemini-1.0-pro')
        
        prompt = "Eres un experto en ventas. Dime 2 productos de cocina virales para TikTok Shop y un hook corto."
        
        response = model.generate_content(prompt)
        
        print("\n" + "🌟" * 10)
        print("RESULTADO DEL ANÁLISIS:")
        print(response.text)
        print("🌟" * 10)
        
    except Exception as e:
        print(f"Error detectado: {e}")
        print("\n--- POSIBLE SOLUCIÓN ---")
        print("Si el error persiste, es probable que la API KEY necesite ser revisada en Google AI Studio.")

if __name__ == "__main__":
    ejecutar()
