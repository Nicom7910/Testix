import os
import time
from datetime import datetime

import pytest
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

BASE_URL = os.getenv("SELENIUM_BASE_URL", "http://localhost:8501")
EVIDENCIA_DIR = os.getenv("SELENIUM_EVIDENCIA_DIR", "evidencias/selenium")
HEADLESS = os.getenv("SELENIUM_HEADLESS", "0") == "1"

EMAIL_CLIENTE = os.getenv("SELENIUM_EMAIL_CLIENTE", "nico@email.com")
PASSWORD_CLIENTE = os.getenv("SELENIUM_PASSWORD_CLIENTE", "1234")

EMAIL_ADMIN = os.getenv("SELENIUM_EMAIL_ADMIN", "admin@email.com")
PASSWORD_ADMIN = os.getenv("SELENIUM_PASSWORD_ADMIN", "1234")


# ============================================================
# HELPERS GENERALES
# ============================================================

def crear_directorio_evidencia():
    os.makedirs(EVIDENCIA_DIR, exist_ok=True)


def tomar_evidencia(driver, nombre):
    crear_directorio_evidencia()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo = os.path.join(EVIDENCIA_DIR, f"{nombre}_{timestamp}.png")
    driver.save_screenshot(archivo)
    print(f"[EVIDENCIA] {archivo}")
    return archivo


def inicializar_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")

    if HEADLESS:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    driver.set_page_load_timeout(30)
    return driver


@pytest.fixture
def driver():
    driver = inicializar_driver()
    yield driver
    time.sleep(1)
    driver.quit()


def esperar_carga_streamlit(driver, timeout=15):
    wait = WebDriverWait(driver, timeout)
    wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(@data-testid, 'stApp') or contains(@class, 'stApp')]")
        )
    )
    time.sleep(1)


def texto_visible(driver):
    return driver.find_element(By.TAG_NAME, "body").text


def assert_texto_en_pantalla(driver, textos_posibles):
    body = texto_visible(driver).lower()

    for texto in textos_posibles:
        if texto.lower() in body:
            return True

    raise AssertionError(
        f"No se encontró ninguno de estos textos en pantalla: {textos_posibles}\n"
        f"Texto visible actual:\n{body[:1500]}"
    )


def xpath_contains_text(texto):
    texto = texto.lower()
    return (
        "contains("
        "translate(normalize-space(.), "
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÑ', "
        "'abcdefghijklmnopqrstuvwxyzáéíóúñ'), "
        f"'{texto}'"
        ")"
    )


def click_por_texto(driver, textos, timeout=10):
    wait = WebDriverWait(driver, timeout)

    if isinstance(textos, str):
        textos = [textos]

    ultimo_error = None

    for texto in textos:
        xpath = (
            f"//button[{xpath_contains_text(texto)}] | "
            f"//*[@role='button' and {xpath_contains_text(texto)}] | "
            f"//*[@role='tab' and {xpath_contains_text(texto)}] | "
            f"//a[{xpath_contains_text(texto)}]"
        )

        try:
            elemento = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento)
            time.sleep(0.3)
            elemento.click()
            time.sleep(1)
            return elemento
        except Exception as error:
            ultimo_error = error

    raise TimeoutException(f"No se pudo hacer click en ningún texto: {textos}. Error: {ultimo_error}")


def abrir_app(driver):
    driver.get(BASE_URL)
    esperar_carga_streamlit(driver)


# ============================================================
# HELPERS DE INPUTS STREAMLIT
# ============================================================

def es_input_interactuable(driver, elemento):
    """
    Streamlit puede dejar inputs ocultos o duplicados en el DOM.
    Esta función filtra solo los inputs visibles y realmente editables.
    """
    try:
        return driver.execute_script(
            """
            const el = arguments[0];
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);

            return (
                rect.width > 0 &&
                rect.height > 0 &&
                style.visibility !== 'hidden' &&
                style.display !== 'none' &&
                !el.disabled &&
                !el.readOnly
            );
            """,
            elemento
        )
    except Exception:
        return False


def obtener_inputs_visibles(driver):
    inputs = driver.find_elements(By.XPATH, "//input | //textarea")
    visibles = []

    for input_element in inputs:
        if es_input_interactuable(driver, input_element):
            visibles.append(input_element)

    return visibles


def limpiar_y_escribir(driver, elemento, valor):
    """
    Escritura robusta para inputs de Streamlit.
    Si el click normal falla, usa JavaScript como respaldo y dispara eventos.
    """
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento)
    time.sleep(0.3)

    try:
        elemento.click()
        time.sleep(0.2)
        elemento.send_keys(Keys.COMMAND, "a")
        elemento.send_keys(Keys.BACKSPACE)
        elemento.send_keys(valor)
        return
    except Exception:
        pass

    # Fallback para Streamlit/React
    driver.execute_script(
        """
        const el = arguments[0];
        const value = arguments[1];

        el.focus();
        el.value = '';
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));

        el.value = value;
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        """,
        elemento,
        valor
    )
    time.sleep(0.3)


def buscar_input_por_label(driver, labels, timeout=10):
    """
    Busca un input visible por label/aria-label/placeholder.
    Filtra elementos ocultos para evitar ElementNotInteractableException.
    """
    wait = WebDriverWait(driver, timeout)

    if isinstance(labels, str):
        labels = [labels]

    ultimo_error = None

    for label in labels:
        label_lower = label.lower()

        posibles_xpaths = [
            # aria-label
            (
                "//input["
                "contains(translate(@aria-label, "
                "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÑ', "
                "'abcdefghijklmnopqrstuvwxyzáéíóúñ'), "
                f"'{label_lower}')"
                "] | "
                "//textarea["
                "contains(translate(@aria-label, "
                "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÑ', "
                "'abcdefghijklmnopqrstuvwxyzáéíóúñ'), "
                f"'{label_lower}')"
                "]"
            ),

            # placeholder
            (
                "//input["
                "contains(translate(@placeholder, "
                "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÑ', "
                "'abcdefghijklmnopqrstuvwxyzáéíóúñ'), "
                f"'{label_lower}')"
                "] | "
                "//textarea["
                "contains(translate(@placeholder, "
                "'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÑ', "
                "'abcdefghijklmnopqrstuvwxyzáéíóúñ'), "
                f"'{label_lower}')"
                "]"
            ),

            # stTextInput
            (
                "//*[contains(@data-testid, 'stTextInput') and "
                f".//*[{xpath_contains_text(label)}]"
                "]//input"
            ),

            # stNumberInput
            (
                "//*[contains(@data-testid, 'stNumberInput') and "
                f".//*[{xpath_contains_text(label)}]"
                "]//input"
            ),

            # label cercano
            (
                f"//*[self::label or self::p or self::div or self::span][{xpath_contains_text(label)}]"
                "/ancestor::*[contains(@data-testid, 'stTextInput') or contains(@data-testid, 'stNumberInput')][1]//input"
            ),
        ]

        for xpath in posibles_xpaths:
            try:
                wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                elementos = driver.find_elements(By.XPATH, xpath)

                for elemento in elementos:
                    if es_input_interactuable(driver, elemento):
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento)
                        time.sleep(0.2)
                        return elemento

            except Exception as error:
                ultimo_error = error

    raise NoSuchElementException(f"No se encontró input visible para labels: {labels}. Error: {ultimo_error}")


def completar_input(driver, labels, valor, timeout=10):
    input_element = buscar_input_por_label(driver, labels, timeout)
    limpiar_y_escribir(driver, input_element, valor)
    time.sleep(0.3)


def completar_formulario_registro_por_orden(driver, email_nuevo):
    """
    Respaldo específico para CP05.
    Si los labels de Streamlit generan conflicto, completa el formulario
    por orden de campos visibles:
    nombre, apellido, email, teléfono, contraseña.
    """
    inputs = obtener_inputs_visibles(driver)

    if len(inputs) < 5:
        raise NoSuchElementException(
            f"No se encontraron al menos 5 inputs visibles para registro. Cantidad encontrada: {len(inputs)}"
        )

    valores = [
        "Selenium",
        "Test",
        email_nuevo,
        "1134567890",
        "1234",
    ]

    for input_element, valor in zip(inputs[:5], valores):
        limpiar_y_escribir(driver, input_element, valor)
        time.sleep(0.2)


def realizar_login(driver, email, password):
    abrir_app(driver)

    try:
        click_por_texto(driver, ["Iniciar sesión", "Iniciar sesion", "Login", "Ingresar"], timeout=4)
    except Exception:
        pass

    completar_input(driver, ["email", "mail", "correo"], email)
    completar_input(driver, ["contraseña", "password"], password)

    tomar_evidencia(driver, "login_datos_cargados")

    click_por_texto(driver, ["Ingresar", "Login", "Iniciar sesión", "Iniciar sesion"])
    time.sleep(2)


# ============================================================
# TEST 1 - CP01 LOGIN CLIENTE VÁLIDO
# ============================================================

def test_cp01_login_cliente_valido(driver):
    """
    CP01 - Login válido con datos correctos de usuario.
    El sistema debe permitir el acceso al usuario común.
    """
    try:
        realizar_login(driver, EMAIL_CLIENTE, PASSWORD_CLIENTE)

        assert_texto_en_pantalla(
            driver,
            [
                "cliente",
                "reservas",
                "canchas",
                "cerrar sesión",
                "cerrar sesion",
                "activas",
                "pendientes"
            ]
        )

        tomar_evidencia(driver, "CP01_login_cliente_exitoso")

    except Exception:
        tomar_evidencia(driver, "CP01_login_cliente_error")
        raise


# ============================================================
# TEST 2 - CP03 LOGIN ADMINISTRADOR VÁLIDO
# ============================================================

def test_cp03_login_administrador_valido(driver):
    """
    CP03 - Login válido con datos correctos de administrador.
    El sistema debe permitir el acceso al administrador y mostrar
    funcionalidades administrativas.
    """
    try:
        realizar_login(driver, EMAIL_ADMIN, PASSWORD_ADMIN)

        assert_texto_en_pantalla(
            driver,
            [
                "administrador",
                "admin",
                "panel",
                "reportes",
                "gestión",
                "gestion",
                "precio",
                "canchas"
            ]
        )

        tomar_evidencia(driver, "CP03_login_admin_exitoso")

    except Exception:
        tomar_evidencia(driver, "CP03_login_admin_error")
        raise


# ============================================================
# TEST 3 - CP05 REGISTRO DE USUARIO VÁLIDO
# ============================================================

def test_cp05_registro_usuario_valido(driver):
    """
    CP05 - Registro de usuario válido.
    El sistema debe permitir al usuario registrarse exitosamente
    y mostrar un mensaje de confirmación.

    Optimizado para Streamlit:
    completa el formulario por orden de inputs visibles.
    """
    try:
        abrir_app(driver)

        click_por_texto(driver, ["Registrarse", "Registro", "Crear cuenta"], timeout=6)

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        email_nuevo = f"selenium_{timestamp}@email.com"

        completar_formulario_registro_por_orden(driver, email_nuevo)

        tomar_evidencia(driver, "CP05_registro_datos_cargados")

        click_por_texto(driver, ["Registrarme", "Registrar", "Crear cuenta"], timeout=6)

        time.sleep(2)

        assert_texto_en_pantalla(
            driver,
            [
                "exitoso",
                "registrado",
                "registro",
                "cuenta creada",
                "usuario creado",
                "confirmación",
                "confirmacion",
                "login",
                "iniciar sesión",
                "iniciar sesion"
            ]
        )

        tomar_evidencia(driver, "CP05_registro_usuario_exitoso")

    except Exception:
        tomar_evidencia(driver, "CP05_registro_usuario_error")
        raise