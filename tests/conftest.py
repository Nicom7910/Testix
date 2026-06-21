import json
import os
import shutil
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.main import app


RUTA_DATA = "app/data"
RUTA_BACKUP = "app/data_backup_tests"

RUTA_USUARIOS = "app/data/usuarios.json"
RUTA_CANCHAS = "app/data/canchas.json"
RUTA_RESERVAS = "app/data/reservas.json"


@pytest.fixture(scope="function")
def client():
    """
    Crea un cliente de pruebas de FastAPI.

    Antes de cada test:
    - Hace backup de los datos reales.
    - Carga datos controlados de prueba.

    Después de cada test:
    - Restaura los datos reales.
    """

    hacer_backup_data()
    cargar_datos_de_prueba()

    cliente = TestClient(app)

    yield cliente

    restaurar_data()


def hacer_backup_data():
    if os.path.exists(RUTA_BACKUP):
        shutil.rmtree(RUTA_BACKUP)

    if os.path.exists(RUTA_DATA):
        shutil.copytree(RUTA_DATA, RUTA_BACKUP)
    else:
        os.makedirs(RUTA_DATA, exist_ok=True)


def restaurar_data():
    if os.path.exists(RUTA_DATA):
        shutil.rmtree(RUTA_DATA)

    if os.path.exists(RUTA_BACKUP):
        shutil.copytree(RUTA_BACKUP, RUTA_DATA)
        shutil.rmtree(RUTA_BACKUP)
    else:
        os.makedirs(RUTA_DATA, exist_ok=True)


def guardar_json(ruta, datos):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)

    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, indent=4, ensure_ascii=False)


def cargar_datos_de_prueba():
    usuarios = [
        {
            "id": 1,
            "nombre": "Admin",
            "apellido": "Testing",
            "email": "admin@test.com",
            "telefono": "1111111111",
            "password": "admin123",
            "rol": "ADMINISTRADOR",
            "activo": True
        },
        {
            "id": 2,
            "nombre": "Nicolas",
            "apellido": "Cliente",
            "email": "nico@test.com",
            "telefono": "2222222222",
            "password": "cliente123",
            "rol": "COMUN",
            "activo": True
        },
        {
            "id": 3,
            "nombre": "Usuario",
            "apellido": "Baja",
            "email": "baja@test.com",
            "telefono": "3333333333",
            "password": "baja123",
            "rol": "COMUN",
            "activo": False
        }
    ]

    canchas = [
        {
            "id": 1,
            "nombre": "Cancha 1",
            "tipo_superficie": "Polvo de ladrillo",
            "techada": False,
            "precio_por_hora": 20000,
            "precio_diurno": 20000,
            "precio_nocturno": 24000,
            "activa": True
        },
        {
            "id": 2,
            "nombre": "Cancha 2",
            "tipo_superficie": "Cemento",
            "techada": True,
            "precio_por_hora": 30000,
            "precio_diurno": 30000,
            "precio_nocturno": 36000,
            "activa": True
        },
        {
            "id": 3,
            "nombre": "Cancha deshabilitada",
            "tipo_superficie": "Sintético",
            "techada": False,
            "precio_por_hora": 25000,
            "precio_diurno": 25000,
            "precio_nocturno": 30000,
            "activa": False
        }
    ]

    reservas = [
        {
            "id": 1,
            "usuario_id": 2,
            "cancha_id": 1,
            "fecha": "2026-12-20",
            "hora_inicio": "10:00:00",
            "hora_fin": "11:00:00",
            "cantidad_horas": 1,
            "monto_total": 20000,
            "sena": 10000,
            "estado_reserva": "confirmada",
            "estado_pago": "pagado",
            "activa": True,
            "pagada": True,
            "motivo_cancelacion": None,
            "fecha_creacion": "2026-06-19 10:00:00",
            "requiere_devolucion": False,
            "monto_devolucion": 0,
            "estado_devolucion": "no_aplica"
        },
        {
            "id": 2,
            "usuario_id": 2,
            "cancha_id": 1,
            "fecha": "2026-12-21",
            "hora_inicio": "15:00:00",
            "hora_fin": "16:30:00",
            "cantidad_horas": 1.5,
            "monto_total": 30000,
            "sena": 15000,
            "estado_reserva": "pendiente",
            "estado_pago": "pendiente",
            "activa": False,
            "pagada": False,
            "motivo_cancelacion": None,
            "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "requiere_devolucion": False,
            "monto_devolucion": 0,
            "estado_devolucion": "no_aplica"
        }
    ]

    guardar_json(RUTA_USUARIOS, usuarios)
    guardar_json(RUTA_CANCHAS, canchas)
    guardar_json(RUTA_RESERVAS, reservas)