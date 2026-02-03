import os
import requests
import json

def ejecutar_bot_definitivo():
    api_key = os.environ.get("GEMINI_API_KEY")
    
    # Jerarquía de modelos para evitar el error 404
    # Si uno no existe en tu región o versión, el bot salta al siguiente
    modelos_a_probar = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-pro"
    ]
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{"text": "Analiza las tendencias de TikTok Shop USA de hoy febrero 2026. Dime los 3 productos de cocina más vendidos, su gancho (hook) y por qué funcionan. Responde en español."}]
        }]
    }

    print("--- INICIANDO PROTOCOLO DE CONEXIÓN TOTAL ---")
    
    exito = False
    for modelo in modelos_a_probar:
        if exito: break
        
        # Probamos tanto la ruta v1 como v1beta automáticamente
        for version in ["v1", "v1beta"]:
            url = f"https://generativelanguage.googleapis.com/{version}/models/{modelo}:generateContent?key={api_key}"
            
            try:
                print(f"Probando: {modelo} vía {version}...")
                response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
                
                if response.status_code == 200:
                    resultado = response.json()
                    texto = resultado['candidates'][0]['content']['parts'][0]['text']
                    
                    print("\n" + "🌟" * 15)
                    print(f"SISTEMA ONLINE - MODELO: {modelo}")
                    print(texto)
                    print("🌟" * 15)
                    
                    exito = True
                    break
                else:
                    print(f"Respuesta {response.status_code} en {modelo}")
            except Exception as e:
                continue

    if not exito:
        print("❌ ERROR CRÍTICO: No se pudo conectar con ningún nodo de Google.")
        print("REVISIÓN FINAL: Asegúrate que tu API KEY en Secrets no tenga espacios y sea válida.")

if __name__ == "__main__":
    ejecutar_bot_definitivo()
