import random
import time
import json
import os
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from pymongo import MongoClient

USE_PYAUTOGUI = os.environ.get("DISPLAY") is not None
if USE_PYAUTOGUI:
    import pyautogui

# Configuración para el scraper, url y demás
URL = "https://www.waze.com/es-419/live-map/"
CHROMEDRIVER_PATH = "/usr/bin/chromedriver"
PIXELS_PER_MOVE = 300
MAX_ALERTAS = 10000

DIRECCIONES = {
    "arriba": (0, PIXELS_PER_MOVE),
    "abajo": (0, -PIXELS_PER_MOVE),
    "izquierda": (-PIXELS_PER_MOVE, 0),
    "derecha": (PIXELS_PER_MOVE, 0),
}
# aca se analiza el mapa y se buscan las alertas desde el network
def analizar_red(driver, alertas):
    print("📡 Analizando solicitudes de red...")
    for request in driver.requests:
        if request.response and request.url.split('?')[0].endswith("georss"):
            try:
                body = request.response.body.decode('utf-8')
                data = json.loads(body)
                if 'alerts' in data:
                    for alerta in data['alerts']:
                        alerta.pop('comments', None)
                        alertas.append(alerta)
                        if len(alertas) >= MAX_ALERTAS:
                            print("🚨 Se alcanzó el límite de 10,000 alertas.")
                            return True
            except Exception as e:
                print(f"⚠️ Error al procesar respuesta: {e}")
    return False

def main():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")

    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(URL)
    time.sleep(5)

    try:
        acknowledge_button = driver.find_element(By.CLASS_NAME, "waze-tour-tooltip__acknowledge")
        acknowledge_button.click()
    except Exception:
        pass

    time.sleep(2)
    if USE_PYAUTOGUI:
        screenWidth, screenHeight = pyautogui.size()
        center_x = screenWidth // 2
        center_y = screenHeight // 2
        pyautogui.click(center_x, center_y)
    else:
        center_x = center_y = 500  # Valores ficticios

    time.sleep(1)

    try:
        print("🔍 Haciendo zoom al mapa...")
        zoom_in_button = driver.find_element(By.CLASS_NAME, "leaflet-control-zoom-in")
        for _ in range(1):
            zoom_in_button.click()
            time.sleep(1)
    except Exception as e:
        print(f"⚠️ Error al hacer zoom: {e}")

    alertas = []
    print("🔄 Iniciando movimientos aleatorios del mapa...")

    while len(alertas) < MAX_ALERTAS:
        direccion = random.choice(list(DIRECCIONES.keys()))
        dx, dy = DIRECCIONES[direccion]

        try:
            if USE_PYAUTOGUI:
                print(f"🧭 Moviendo hacia: {direccion}")
                pyautogui.moveTo(center_x, center_y)
                pyautogui.mouseDown()
                pyautogui.moveRel(dx, dy, duration=0.5)
                pyautogui.mouseUp()
                time.sleep(3)
            else:
                print(f"🧭 (Simulado) Movimiento hacia: {direccion}")
                time.sleep(1)

            if analizar_red(driver, alertas):
                break
        except Exception as e:
            print(f"⚠️ Error al mover el mapa: {e}")

    driver.quit()

    # Guardar alertas en MongoDB -> container mongo
    if alertas:
        try:
            print("💾 Conectando a MongoDB...")
            client = MongoClient("mongodb://admin:admin123@mongo:27017/")
            db = client["waze_db"]
            collection = db["alertas"]

            result = collection.insert_many(alertas)
            print(f"\n✅ Se insertaron {len(result.inserted_ids)} alertas en MongoDB.")
        except Exception as e:
            print(f"❌ Error al guardar en MongoDB: {e}")
    else:
        print("⚠️ No se encontraron alertas para guardar.")

    print("✅ Navegación finalizada.")

if __name__ == "__main__":
    main()
