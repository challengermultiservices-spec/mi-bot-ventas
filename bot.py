import os
import requests
import json

def ejecutar_diagnostico_y_bot():
    api_key = os.environ.get("GEMINI_API_KEY")
    base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    print("--- PROTOCOLO DE AUTO-DESCUBRIMIENTO ---")
    
    try:
        # PASO 1: Preguntar a Google qué modelos ve esta llave
        print("Consultando modelos disponibles para tu cuenta...")
        list_url = f"{base_url}/models?key={api_key}"
        res = requests.get(list_url)
        
        if res.status_code != 200:
            print(f"❌ Error de cuenta ({res.status_code}): {res.text}")
            return

        modelos = res.json().get('models', [])
        if not modelos:
            print("❌ Tu llave no tiene acceso a ningún modelo. Revisa AI Studio.")
            return

        # PASO 2: Usar el primer modelo disponible que soporte generación
        modelo_activo = None
        for m in modelos:
            if "generateContent" in m.get('supportedGenerationMethods', []):
                modelo_activo = m['name'] # Ya viene como 'models/gemini-...'
                break
        
        if not modelo_activo:
            print("❌ No se encontró un modelo con permisos de escritura.")
            return

        print(f"✅ Modelo detectado y listo: {modelo_activo}")

        # PASO 3: Ejecutar la consulta con el modelo que SÍ existe
        url_gen = f"https://generativelanguage.googleapis.com/v1beta/{modelo_activo}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": "Dime 2 productos de cocina virales en TikTok Shop USA hoy."}]}]
        }
        
        response = requests.post(url_gen, json=payload)
        resultado = response.json()
        
        print("\n" + "🚀" * 10)
        print(resultado['candidates'][0]['content']['parts'][0]['text'])
        print("🚀" * 10)

    except Exception as e:
        print(f"Fallo general: {e}")

if __name__ == "__main__":
    ejecutar_diagnostico_y_bot()
