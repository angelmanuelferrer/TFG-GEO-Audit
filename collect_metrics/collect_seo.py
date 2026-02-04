import requests
import json
import os
from datetime import datetime

# CONFIGURACIÓN
URL_OBJETIVO = "https://programamos.es/"
# Si no hay API key en el entorno, el script fallará o Google limitará las peticiones
API_KEY = os.environ.get("PAGESPEED_API_KEY") 

def obtener_metricas(estrategia):
    """
    Estrategia puede ser 'mobile' o 'desktop'
    """
    url_api = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={URL_OBJETIVO}&strategy={estrategia}&key={API_KEY}"
    response = requests.get(url_api)
    return response.json()

def main():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    print(f"[{timestamp}] Iniciando auditoría para {URL_OBJETIVO}...")
    datos_mobile = obtener_metricas("mobile")
    datos_desktop = obtener_metricas("desktop")
    resultado_final = {
        "fecha": timestamp,
        "url": URL_OBJETIVO,
        "mobile": {
            "performance_score": datos_mobile["lighthouseResult"]["categories"]["performance"]["score"],
            "seo_score": datos_mobile["lighthouseResult"]["categories"]["seo"]["score"],
            "lcp": datos_mobile["lighthouseResult"]["audits"]["largest-contentful-paint"]["displayValue"],
            "tbt": datos_mobile["lighthouseResult"]["audits"]["total-blocking-time"]["displayValue"]
        },
        "desktop": {
            "performance_score": datos_desktop["lighthouseResult"]["categories"]["performance"]["score"],
            "seo_score": datos_desktop["lighthouseResult"]["categories"]["seo"]["score"]
        }
    }

    # 3. Guardar en carpeta 'data'
    os.makedirs("data/seo", exist_ok=True)
    nombre_archivo = f"data/seo/metrics_{timestamp}.json"
    
    with open(nombre_archivo, "w") as f:
        json.dump(resultado_final, f, indent=4)
    
    print(f"¡Éxito! Datos guardados en {nombre_archivo}")

if __name__ == "__main__":
    main()