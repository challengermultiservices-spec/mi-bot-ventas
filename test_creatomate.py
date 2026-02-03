import os, requests, json

def test_conexion():
    # Verifica que este ID coincida con el de tu panel de Creatomate
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"
    api_key = os.environ.get("CREATOMATE_API_KEY", "").strip()

    print(f"--- INICIANDO TEST DE CONEXION ---")
    
    url = "https://api.creatomate.com/v2/renders"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "template_id": TEMPLATE_ID,
        "modifications": {
            "Text-1.text": "TEST EXITOSO",
            "Text-2.text": "La conexion entre Github y Creatomate funciona."
        }
    }

    try:
        # Quitamos cualquier formato extraño de la URL con strip()
        response = requests.post(url.strip(), headers=headers, json=payload, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code in [200, 201, 202]:
            print("✅ ¡CONEXIÓN EXITOSA!")
            print(f"URL del Video: {response.json()[0]['url']}")
        else:
            print(f"❌ ERROR DE API: {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR DE RED: {e}")

if __name__ == "__main__":
    test_conexion()
