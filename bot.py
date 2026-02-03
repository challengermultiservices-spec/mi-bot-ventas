import os
import requests
import json

def ejecutar():
    api_key = os.environ.get("GEMINI_API_KEY")
    # Usamos la URL directa de la API de Google
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    print("Enviando petición directa a los servidores de Google...")

    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{
            "parts": [{"text": "Dime 2 productos de cocina virales para TikTok Shop USA y un hook de 3 segundos para cada uno."}]
        }]
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        resultado = response.json()
        
        # Extraemos el texto de la respuesta
        texto = resultado['candidates'][0]['content']['parts'][0]['text']
        
        print("\n" + "🚀" * 10)
        print("¡LO LOGRAMOS! AQUÍ TIENES TUS PRODUCTOS:")
        print(texto)
        print("🚀" * 10)

    except Exception as e:
        print(f"Error en la conexión directa: {e}")
        print("Respuesta del servidor:", response.text)

if __name__ == "__main__":
    ejecutar()
