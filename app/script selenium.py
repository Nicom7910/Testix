import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- Configuración Inicial ---
BASE_URL = "http://localhost:3000"  # Cambia esto por la URL de tu frontend
EVIDENCIA_DIR = "evidencia"

# Crear directorio de evidencia si no existe
if not os.path.exists(EVIDENCIA_DIR):
    os.makedirs(EVIDENCIA_DIR)


def tomar_evidencia(driver, nombre_flujo):
    """Guarda una captura de pantalla con marca de tiempo."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(EVIDENCIA_DIR, f"{nombre_flujo}_{timestamp}.png")
    driver.save_screenshot(file_path)
    print(f"[EVIDENCIA] Captura guardada en: {file_path}")


def inicializar_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    # Configura el ChromeDriver automáticamente
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver


# --- Flujos de Automatización ---

def automatizar_registro(driver):
    print("\n--- Iniciando Flujo de Registro de Usuario ---")
    driver.get(f"{BASE_URL}/registro")  # Ajustar a la ruta real de tu registro
    
    wait = WebDriverWait(driver, 10)
    
    # Rellenar formulario de registro (Asumiendo IDs estándar)
    nombre_input = wait.until(EC.presence_of_element_located((By.ID, "nombre")))
    email_input = driver.find_element(By.ID, "email")
    password_input = driver.find_element(By.ID, "password")
    btn_registrar = driver.find_element(By.ID, "btn-registrar")
    
    nombre_input.send_keys("Juan Perez")
    email_input.send_keys("juan.perez@example.com")
    password_input.send_keys("Password123*")
    
    # Tomar evidencia antes de enviar
    tomar_evidencia(driver, "1_registro_datos_completos")
    
    btn_registrar.click()
    
    # Esperar confirmación o redirección
    time.sleep(2) 
    tomar_evidencia(driver, "2_registro_exitoso")
    print("[OK] Flujo de registro completado.")


def automatizar_login(driver):
    print("\n--- Iniciando Flujo de Login ---")
    driver.get(f"{BASE_URL}/login")
    
    wait = WebDriverWait(driver, 10)
    
    email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
    password_input = driver.find_element(By.ID, "password")
    btn_login = driver.find_element(By.ID, "btn-login")
    
    email_input.send_keys("juan.perez@example.com")
    password_input.send_keys("Password123*")
    
    tomar_evidencia(driver, "3_login_datos_completos")
    btn_login.click()
    
    # Esperar que cargue el dashboard/inicio tras loguearse
    wait.until(EC.presence_of_element_located((By.ID, "dashboard-bienvenida")))
    tomar_evidencia(driver, "4_login_exitoso")
    print("[OK] Flujo de Login completado.")


def automatizar_reserva(driver):
    print("\n--- Iniciando Flujo de Reserva de Cancha ---")
    # Ir a la sección de reservas
    driver.get(f"{BASE_URL}/reservas")
    
    wait = WebDriverWait(driver, 10)
    
    # Seleccionar cancha, fecha y hora (Asumiendo elementos del formulario)
    select_cancha = wait.until(EC.presence_of_element_located((By.ID, "select-cancha")))
    select_cancha.send_keys("Cancha Rápida 1") # Selecciona por texto o valor si es un <select>
    
    fecha_input = driver.find_element(By.ID, "fecha-reserva")
    fecha_input.send_keys("25/06/2026") # Formato según tu input de frontend
    
    hora_input = driver.find_element(By.ID, "hora-reserva")
    hora_input.send_keys("18:00")
    
    tomar_evidencia(driver, "5_reserva_datos_completos")
    
    btn_reservar = driver.find_element(By.ID, "btn-confirmar-reserva")
    btn_reservar.click()
    
    # Esperar mensaje de éxito de la reserva
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "alert-success")))
    tomar_evidencia(driver, "6_reserva_exitosa")
    print("[OK] Flujo de Reserva completado con éxito.")


# --- Ejecución Principal ---
if __name__ == "__main__":
    driver = inicializar_driver()
    try:
        # Ejecución secuencial del flujo de pruebas
        automatizar_registro(driver)
        automatizar_login(driver)
        automatizar_reserva(driver)
        
        print("\n[ÉXITO] Todos los flujos se automatizaron y la evidencia fue generada.")
        
    except Exception as e:
        print(f"\n[ERROR] Ocurrió un fallo durante la automatización: {e}")
        tomar_evidencia(driver, "ERROR_PROCESO")
        
    finally:
        # Cerrar el navegador al finalizar
        time.sleep(3)
        driver.quit()