import os
import requests
import json

def ejecutar():
    api_key = os.environ.get("GEMINI_API_KEY")
    
    # CAMBIO CRUCIAL: Usamos la versión 'v1' y el modelo exacto de producción
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    print("Conectando con la API de Producción de Google (v1)...")

    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{
            "parts": [{"text": "Actúa como experto en TikTok Shop. Dime 2 productos de cocina virales hoy 2 de febrero de 2026 y un hook para cada uno."}]
        }]
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        
        # Si el servidor responde con error, lo atrapamos aquí
        if response.status_code != 200:
            print(f"Error del servidor ({response.status_code}): {response.text}")
            return

        resultado = response.json()
        
        # Extraemos el texto de la respuesta
        texto = resultado['candidates'][0]['content']['parts'][0]['text']
        
        print("\n" + "✅" * 10)
        print("¡POR FIN! AQUÍ TIENES TUS PRODUCTOS:")
        print(texto)
        print("✅" * 10)

    except Exception as e:
        print(f"Error inesperado: {e}")

if __name__ == "__main__":
    ejecutar()
