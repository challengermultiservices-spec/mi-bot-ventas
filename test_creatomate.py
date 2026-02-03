import os, requests, json

def test_conexion():
    # ID de tu plantilla de Creatomate
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"
    api_key = str(os.environ.get("CREATOMATE_API_KEY", "")).strip()

    print("--- INICIANDO TEST DE CONEXION BLINDADO ---")
    url = "https://api.creatomate.com/v2/renders"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0" # Esto evita el Error 0 en muchos casos
    }
    
    payload = {
        "template_id": TEMPLATE_ID,
        "modifications": {
            "Text-1.text": "TEST DE CONEXION",
            "Text-2.text": "Si ves esto, la API Key y el ID funcionan perfectamente."
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code in [200, 201, 202]:
            print("✅ ¡CONEXIÓN EXITOSA!")
            print(f"URL del Video: {response.json()[0]['url']}")
        else:
            print(f"❌ ERROR DE API: {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR DE RED (Causa del Error 0): {e}")

if __name__ == "__main__":
    test_conexion()
