import os, requests, json

def test_conexion():
    # ID de tu plantilla
    TEMPLATE_ID = "3a6f8698-dd48-4a5f-9cad-5b00b206b6b8"
    # Cargamos la Key limpiando espacios
    api_key = str(os.environ.get("CREATOMATE_API_KEY", "")).strip()

    print(f"--- INICIANDO TEST DE CONEXION BLINDADO ---")
    
    url = "https://api.creatomate.com/v2/renders"
    
    # Añadimos Headers de un navegador real para evitar el Error 0
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    payload = {
        "template_id": TEMPLATE_ID,
        "modifications": {
            "Text-1.text": "PROBANDO CONEXION",
            "Text-2.text": "Si ves este video, hemos vencido al Error 0."
        }
    }

    try:
        # Forzamos la petición ignorando errores de SSL temporales
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"Status Code recibido: {response.status_code}")
        
        if response.status_code in [200, 201, 202]:
            print("✅ ¡CONEXIÓN EXITOSA!")
            print(f"URL del Video: {response.json()[0]['url']}")
        else:
            print(f"❌ ERROR DE API ({response.status_code}): {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR DE RED (Causa del 0): {e}")

if __name__ == "__main__":
    test_conexion()
