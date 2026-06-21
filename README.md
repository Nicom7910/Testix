# Testix - Sistema de Reserva de Canchas de Tenis

Sistema web para la gestión de reservas de canchas de tenis.

El sistema permite registrar usuarios, iniciar sesión, consultar disponibilidad de canchas, crear reservas, pagar una seña, cancelar reservas y consultar historial. Además, permite al administrador gestionar canchas, modificar precios, consultar reservas y generar reportes.

Este proyecto fue desarrollado como trabajo práctico para la materia **Testing de Aplicaciones**.

---

## 1. Tecnologías utilizadas

- Python
- FastAPI
- Streamlit
- SQLAlchemy
- Pytest
- Pytest-cov
- Selenium
- Webdriver Manager
- JMeter
- JSON como almacenamiento de datos
- Git / GitHub

---

## 2. Estructura general del proyecto

```txt
Testix/
├── app/
│   ├── data/
│   │   ├── canchas.json
│   │   ├── reservas.json
│   │   └── usuarios.json
│   ├── routes/
│   │   ├── cancha_routes.py
│   │   ├── reporte_routes.py
│   │   ├── reserva_routes.py
│   │   └── usuario_routes.py
│   ├── schemas/
│   ├── utils/
│   │   ├── file_manager.py
│   │   └── logger.py
│   └── main.py
├── frontend/
│   └── streamlit_app.py
├── tests/
│   ├── integration/
│   │   ├── test_api_inicio.py
│   │   ├── test_usuarios_api.py
│   │   ├── test_canchas_api.py
│   │   ├── test_reservas_api.py
│   │   └── test_reportes_api.py
│   └── unit/
│       └── test_reservas_unit.py
├── evidencias/
│   ├── logs/
│   └── tests/
├── logs/
├── requirements.txt
├── pytest.ini
└── README.md
```

---

# 3. Instalación desde cero

## 3.1. Clonar el repositorio

```bash
git clone https://github.com/Nicom7910/Testix.git
```

Ingresar a la carpeta del proyecto:

```bash
cd Testix
```

---

## 3.2. Crear entorno virtual

En Mac/Linux:

```bash
python3 -m venv venv
```

En Windows:

```bash
python -m venv venv
```

---

## 3.3. Activar entorno virtual

En Mac/Linux:

```bash
source venv/bin/activate
```

En Windows:

```bash
venv\Scripts\activate
```

Cuando el entorno esté activo, la terminal debería mostrar algo similar a:

```txt
(venv)
```

---

## 3.4. Verificar que el entorno virtual está activo

Ejecutar:

```bash
which python
which pip
```

En Mac/Linux debería aparecer una ruta similar a:

```txt
.../Testix/venv/bin/python
.../Testix/venv/bin/pip
```

En Windows debería apuntar a la carpeta:

```txt
venv\Scripts\
```

---

## 3.5. Actualizar pip

```bash
python -m pip install --upgrade pip
```

---

## 3.6. Instalar dependencias

```bash
python -m pip install -r requirements.txt
```

El archivo `requirements.txt` debe incluir:

```txt
fastapi
uvicorn
pydantic
email-validator
streamlit
requests
sqlalchemy
pytest
httpx
pytest-cov
selenium
webdriver-manager
```

---

# 4. Ejecutar el backend

Desde la raíz del proyecto, con el entorno virtual activado:

```bash
uvicorn app.main:app --reload
```

La API queda disponible en:

```txt
http://127.0.0.1:8000
```

La documentación Swagger queda disponible en:

```txt
http://127.0.0.1:8000/docs
```

Desde Swagger se pueden probar manualmente los endpoints del backend.

---

# 5. Ejecutar el frontend

Abrir una segunda terminal.

Activar nuevamente el entorno virtual:

```bash
source venv/bin/activate
```

En Windows:

```bash
venv\Scripts\activate
```

Luego ejecutar:

```bash
streamlit run frontend/streamlit_app.py
```

El frontend queda disponible normalmente en:

```txt
http://localhost:8501
```

---

# 6. Flujo básico de uso del sistema

## 6.1. Usuario cliente

El cliente puede:

- Registrarse.
- Iniciar sesión.
- Consultar canchas disponibles.
- Seleccionar cancha, fecha, horario de inicio y horario de fin.
- Crear una reserva.
- Pagar la seña.
- Consultar reservas activas.
- Consultar reservas pendientes.
- Consultar reservas pasadas.
- Consultar reservas canceladas.
- Cancelar sus propias reservas.

---

## 6.2. Administrador

El administrador puede:

- Iniciar sesión.
- Registrar nuevas canchas.
- Modificar datos de canchas.
- Modificar precios.
- Dar de baja canchas.
- Consultar todas las reservas.
- Consultar reservas activas, pendientes, canceladas y pasadas.
- Cancelar reservas de usuarios.
- Consultar reportes generales.

---

# 7. Endpoints principales

## 7.1. Usuarios

```txt
POST /usuarios/
POST /usuarios/login
GET /usuarios/
GET /usuarios/{usuario_id}
PUT /usuarios/{usuario_id}
DELETE /usuarios/{usuario_id}
```

---

## 7.2. Canchas

```txt
POST /canchas/
GET /canchas/
GET /canchas/disponibles
GET /canchas/{cancha_id}
PUT /canchas/{cancha_id}
DELETE /canchas/{cancha_id}
PATCH /canchas/{cancha_id}/precio
```

---

## 7.3. Reservas

```txt
POST /reservas/
GET /reservas/
GET /reservas/activas
GET /reservas/pendientes
GET /reservas/canceladas
GET /reservas/pasadas
GET /reservas/usuario/{usuario_id}/activas
GET /reservas/usuario/{usuario_id}/pendientes
GET /reservas/usuario/{usuario_id}/canceladas
GET /reservas/usuario/{usuario_id}/pasadas
GET /reservas/usuario/{usuario_id}/historial
PUT /reservas/{reserva_id}
PUT /reservas/{reserva_id}/pagar
PUT /reservas/{reserva_id}/cancelar
```

---

## 7.4. Reportes

```txt
GET /reportes/general
```

---

# 8. Logs del sistema

El sistema incorpora logs para registrar eventos relevantes y facilitar el análisis de errores.

El logger se encuentra en:

```txt
app/utils/logger.py
```

El archivo de logs se genera automáticamente en:

```txt
logs/sistema.log
```

---

## 8.1. Ver logs en tiempo real

Con el backend ejecutándose, abrir otra terminal y ejecutar:

```bash
tail -f logs/sistema.log
```

---

## 8.2. Eventos registrados en logs

El sistema registra eventos como:

- Intentos de login.
- Login exitoso.
- Login rechazado.
- Registro de usuarios.
- Consulta de usuarios.
- Accesos rechazados por falta de permisos.
- Creación de reservas.
- Validación de cancha activa.
- Validación de fecha y horario.
- Detección de reservas superpuestas.
- Cálculo de monto total y seña.
- Pago de seña.
- Pago rechazado.
- Cancelación de reservas.
- Cancelación sin devolución.
- Cancelación con devolución pendiente.
- Gestión de canchas.
- Modificación de precios.
- Generación de reportes.
- Errores en filtros de reportes.

---

## 8.3. Ejemplo de log

```txt
2026-06-19 19:52:38 | INFO | testix | Intento de crear reserva | usuario_id=2 | cancha_id=2 | fecha=2026-06-20 | hora_inicio=17:00:00 | hora_fin=18:30:00
2026-06-19 19:52:38 | INFO | testix | Cancha activa encontrada | cancha_id=2
2026-06-19 19:52:38 | INFO | testix | Importes calculados | cancha_id=2 | horas=1.5 | monto_total=64000.0 | sena=32000.0
2026-06-19 19:52:38 | INFO | testix | No se detecto superposicion | cancha_id=2 | fecha=2026-06-20
2026-06-19 19:52:38 | INFO | testix | Reserva creada correctamente | reserva_id=23 | usuario_id=2 | cancha_id=2 | monto_total=64000.0 | sena=32000.0
```

---

## 8.4. Evidencias de logs

Las evidencias formales de logs se encuentran en:

```txt
evidencias/logs/
```

Archivos principales:

```txt
BUG_LOGIN_Y_RESERVA.log
BUG_PAGO_SENA.log
BUG_CONSULTA_RESERVAS.log
README_LOGS.md
```

Estas evidencias sirven para demostrar que el sistema registra información técnica útil para analizar errores y validar flujos críticos.

---

# 9. Pruebas automatizadas

El proyecto incorpora pruebas automatizadas con `pytest`.

Las pruebas están divididas en:

```txt
tests/integration/
tests/unit/
```

---

## 9.1. Tests de integración

Los tests de integración validan el comportamiento completo de los endpoints principales.

Archivos:

```txt
tests/integration/test_api_inicio.py
tests/integration/test_usuarios_api.py
tests/integration/test_canchas_api.py
tests/integration/test_reservas_api.py
tests/integration/test_reportes_api.py
```

Validan:

- Inicio de API.
- Registro de usuarios.
- Login correcto.
- Login incorrecto.
- Permisos de administrador.
- Gestión de usuarios.
- Listado de canchas.
- Consulta de disponibilidad.
- Alta de canchas.
- Modificación de canchas.
- Modificación de precios.
- Baja lógica de canchas.
- Creación de reservas.
- Rechazo de reservas superpuestas.
- Rechazo de reservas con fecha pasada.
- Rechazo de horarios inválidos.
- Pago correcto de seña.
- Rechazo de tarjeta inválida.
- Rechazo de tarjeta vencida.
- Rechazo de pago simulado.
- Cancelación de reservas.
- Rechazo de cancelación sin motivo.
- Reporte general.
- Reportes filtrados por fecha.
- Bloqueo de reportes para usuarios no administradores.

---

## 9.2. Tests unitarios

Los tests unitarios validan funciones internas sin pasar por toda la API.

Archivo:

```txt
tests/unit/test_reservas_unit.py
```

Validan:

- Cálculo de intervalos horarios.
- Manejo de reservas que finalizan a medianoche.
- Detección de superposición.
- Validación de fecha pasada.
- Validación de horarios fuera de rango.
- Cálculo de importes diurnos.
- Cálculo de importes nocturnos.
- Cálculo mixto diurno/nocturno.
- Validación de número de tarjeta.
- Validación de titular.
- Validación de vencimiento.
- Validación de tarjeta vencida.
- Validación de código de seguridad.

---

# 10. Ejecutar tests

## 10.1. Ejecutar todos los tests

Desde la raíz del proyecto:

```bash
python -m pytest
```

---

## 10.2. Ejecutar solo tests de integración

```bash
python -m pytest tests/integration
```

---

## 10.3. Ejecutar solo tests unitarios

```bash
python -m pytest tests/unit
```

---

## 10.4. Ejecutar tests de usuarios

```bash
python -m pytest tests/integration/test_usuarios_api.py
```

---

## 10.5. Ejecutar tests de canchas

```bash
python -m pytest tests/integration/test_canchas_api.py
```

---

## 10.6. Ejecutar tests de reservas

```bash
python -m pytest tests/integration/test_reservas_api.py
```

---

## 10.7. Ejecutar tests de reportes

```bash
python -m pytest tests/integration/test_reportes_api.py
```

---

## 10.8. Ejecutar tests unitarios de reservas

```bash
python -m pytest tests/unit/test_reservas_unit.py
```

---

# 11. Cobertura de tests

Para generar cobertura de tests:

```bash
python -m pytest --cov=app --cov-report=term-missing --cov-report=html
```

Este comando:

1. Ejecuta todos los tests.
2. Muestra la cobertura en la terminal.
3. Genera un reporte HTML.

El reporte HTML queda en:

```txt
htmlcov/index.html
```

---

## 11.1. Abrir reporte de cobertura en Mac

```bash
open htmlcov/index.html
```

---

## 11.2. Abrir reporte de cobertura en Windows

Desde el explorador de archivos, abrir:

```txt
htmlcov/index.html
```

---

## 11.3. Evidencias de cobertura

Las evidencias de tests y cobertura se guardan en:

```txt
evidencias/tests/
```

Archivos esperados:

```txt
README_TESTS.md
RESUMEN_TESTS.md
resultado_pytest_cobertura.png
cobertura_html.png
```

---

# 12. Pruebas con Selenium

El proyecto incluye dependencias para pruebas de interfaz con Selenium:

```txt
selenium
webdriver-manager
```

Estas dependencias permiten automatizar pruebas sobre el navegador.

Para que funcionen correctamente, deben estar instaladas mediante:

```bash
python -m pip install -r requirements.txt
```

---

## 12.1. Recomendación para ejecutar Selenium

Antes de ejecutar pruebas Selenium:

1. Levantar el backend:

```bash
uvicorn app.main:app --reload
```

2. Levantar el frontend:

```bash
streamlit run frontend/streamlit_app.py
```

3. Ejecutar los scripts Selenium correspondientes.

---

# 13. Pruebas con JMeter

El proyecto contempla pruebas de rendimiento con JMeter para validar requerimientos no funcionales.

Se utilizan para evaluar:

- Tiempo de respuesta.
- Disponibilidad.
- Consultas concurrentes.
- Tasa de error.
- Rendimiento de endpoints.

Las evidencias de JMeter se documentan en el material de entrega del proyecto.

---

# 14. Evidencias del proyecto

El proyecto incluye evidencias técnicas en:

```txt
evidencias/
├── logs/
└── tests/
```

---

## 14.1. Evidencias de logs

Ubicación:

```txt
evidencias/logs/
```

Contiene fragmentos representativos de logs generados durante pruebas funcionales.

---

## 14.2. Evidencias de tests

Ubicación:

```txt
evidencias/tests/
```

Contiene:

- Resumen de pruebas automatizadas.
- Comandos utilizados.
- Capturas de ejecución.
- Capturas de cobertura.

---

# 15. Comandos útiles

## Clonar repositorio

```bash
git clone https://github.com/Nicom7910/Testix.git
cd Testix
```

---

## Crear entorno virtual

```bash
python3 -m venv venv
```

---

## Activar entorno virtual en Mac/Linux

```bash
source venv/bin/activate
```

---

## Activar entorno virtual en Windows

```bash
venv\Scripts\activate
```

---

## Instalar dependencias

```bash
python -m pip install -r requirements.txt
```

---

## Levantar backend

```bash
uvicorn app.main:app --reload
```

---

## Levantar frontend

```bash
streamlit run frontend/streamlit_app.py
```

---

## Ejecutar todos los tests

```bash
python -m pytest
```

---

## Ejecutar cobertura

```bash
python -m pytest --cov=app --cov-report=term-missing --cov-report=html
```

---

## Ver logs

```bash
tail -f logs/sistema.log
```

---

# 16. Configuración de pytest

El proyecto utiliza un archivo `pytest.ini` para que Python reconozca correctamente la estructura del proyecto.

Contenido esperado:

```ini
[pytest]
pythonpath = .
testpaths = tests
```

---

# 17. Recomendaciones para desarrollo

Antes de hacer cambios importantes:

```bash
git status
```

Para traer cambios del repositorio remoto:

```bash
git pull --no-rebase origin main
```

Para guardar cambios:

```bash
git add .
git commit -m "Descripcion del cambio"
```

Para subir cambios:

```bash
git push origin main
```

---

# 18. Problemas comunes

## 18.1. Error: No module named pytest

Instalar dependencias:

```bash
python -m pip install -r requirements.txt
```

O instalar pytest manualmente:

```bash
python -m pip install pytest pytest-cov httpx
```

---

## 18.2. Error: No module named app

Verificar que exista `pytest.ini`:

```ini
[pytest]
pythonpath = .
testpaths = tests
```

Ejecutar los tests desde la raíz del proyecto:

```bash
python -m pytest
```

---

## 18.3. El entorno virtual no reconoce python

Recrear el entorno virtual:

```bash
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

---

## 18.4. Selenium aparece como import no resuelto

Instalar dependencias:

```bash
python -m pip install selenium webdriver-manager
```

O reinstalar todo:

```bash
python -m pip install -r requirements.txt
```

---

# 19. Estado actual del proyecto

El sistema cuenta con:

- Backend con FastAPI.
- Frontend con Streamlit.
- Registro de usuarios.
- Login de usuarios.
- Roles de cliente y administrador.
- Gestión de canchas.
- Consulta de disponibilidad.
- Creación de reservas.
- Validación de reservas superpuestas.
- Pago de seña.
- Validación de datos de pago.
- Cancelación de reservas.
- Historial de reservas.
- Reportes generales.
- Logs técnicos.
- Evidencias de logs.
- Tests de integración.
- Tests unitarios.
- Cobertura de tests.
- Dependencias para Selenium.
- Evidencias para entrega.
