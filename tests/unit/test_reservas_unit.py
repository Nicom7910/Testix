from datetime import date, time, timedelta

import pytest
from fastapi import HTTPException

from app.routes.reserva_routes import (
    calcular_importes,
    validar_fecha_y_horario,
    validar_superposicion_reserva,
    validar_pago,
    hay_superposicion,
    obtener_intervalo_datetime,
)
from app.schemas.reserva_schema import PagoReservaRequest


def test_obtener_intervalo_datetime_mismo_dia():
    fecha = date(2026, 12, 20)
    hora_inicio = time(10, 0)
    hora_fin = time(11, 30)

    inicio, fin = obtener_intervalo_datetime(fecha, hora_inicio, hora_fin)

    assert inicio.date() == fecha
    assert fin.date() == fecha
    assert inicio.time() == hora_inicio
    assert fin.time() == hora_fin


def test_obtener_intervalo_datetime_fin_medianoche():
    fecha = date(2026, 12, 20)
    hora_inicio = time(23, 0)
    hora_fin = time(0, 0)

    inicio, fin = obtener_intervalo_datetime(fecha, hora_inicio, hora_fin)

    assert inicio.date() == fecha
    assert inicio.time() == hora_inicio
    assert fin.date() == fecha + timedelta(days=1)
    assert fin.time() == hora_fin


def test_hay_superposicion_true():
    fecha = date(2026, 12, 20)

    inicio_nuevo, fin_nuevo = obtener_intervalo_datetime(
        fecha,
        time(10, 30),
        time(11, 30)
    )

    inicio_existente, fin_existente = obtener_intervalo_datetime(
        fecha,
        time(10, 0),
        time(11, 0)
    )

    assert hay_superposicion(
        inicio_nuevo,
        fin_nuevo,
        inicio_existente,
        fin_existente
    ) is True


def test_hay_superposicion_false():
    fecha = date(2026, 12, 20)

    inicio_nuevo, fin_nuevo = obtener_intervalo_datetime(
        fecha,
        time(12, 0),
        time(13, 0)
    )

    inicio_existente, fin_existente = obtener_intervalo_datetime(
        fecha,
        time(10, 0),
        time(11, 0)
    )

    assert hay_superposicion(
        inicio_nuevo,
        fin_nuevo,
        inicio_existente,
        fin_existente
    ) is False


def test_validar_fecha_y_horario_correcto():
    validar_fecha_y_horario(
        date(2026, 12, 20),
        time(10, 0),
        time(11, 0)
    )


def test_validar_fecha_y_horario_fecha_pasada():
    fecha_pasada = date.today() - timedelta(days=1)

    with pytest.raises(HTTPException) as error:
        validar_fecha_y_horario(
            fecha_pasada,
            time(10, 0),
            time(11, 0)
        )

    assert error.value.status_code == 400
    assert error.value.detail == "No se pueden crear reservas con fecha anterior a la actual"


def test_validar_fecha_y_horario_inicio_fuera_de_rango():
    with pytest.raises(HTTPException) as error:
        validar_fecha_y_horario(
            date(2026, 12, 20),
            time(7, 0),
            time(8, 0)
        )

    assert error.value.status_code == 400
    assert error.value.detail == "La hora de inicio debe estar entre 08:00 y 23:00"


def test_validar_fecha_y_horario_fin_menor_igual_inicio():
    with pytest.raises(HTTPException) as error:
        validar_fecha_y_horario(
            date(2026, 12, 20),
            time(14, 0),
            time(14, 0)
        )

    assert error.value.status_code == 400
    assert error.value.detail == "La hora de fin debe ser mayor a la hora de inicio, excepto si finaliza a las 00:00"


def test_calcular_importes_diurno():
    cancha = {
        "id": 1,
        "precio_diurno": 20000,
        "precio_nocturno": 24000
    }

    cantidad_horas, monto_total, sena = calcular_importes(
        cancha,
        date(2026, 12, 20),
        time(10, 0),
        time(11, 30)
    )

    assert cantidad_horas == 1.5
    assert monto_total == 30000
    assert sena == 15000


def test_calcular_importes_nocturno():
    cancha = {
        "id": 1,
        "precio_diurno": 20000,
        "precio_nocturno": 24000
    }

    cantidad_horas, monto_total, sena = calcular_importes(
        cancha,
        date(2026, 12, 20),
        time(18, 0),
        time(19, 0)
    )

    assert cantidad_horas == 1
    assert monto_total == 24000
    assert sena == 12000


def test_calcular_importes_mixto_diurno_nocturno():
    cancha = {
        "id": 1,
        "precio_diurno": 20000,
        "precio_nocturno": 24000
    }

    cantidad_horas, monto_total, sena = calcular_importes(
        cancha,
        date(2026, 12, 20),
        time(17, 30),
        time(18, 30)
    )

    assert cantidad_horas == 1
    assert monto_total == 22000
    assert sena == 11000


def test_validar_superposicion_reserva_detecta_conflicto():
    reservas = [
        {
            "id": 1,
            "usuario_id": 2,
            "cancha_id": 1,
            "fecha": "2026-12-20",
            "hora_inicio": "10:00:00",
            "hora_fin": "11:00:00",
            "estado_reserva": "confirmada",
            "estado_pago": "pagado",
            "activa": True,
            "pagada": True,
            "motivo_cancelacion": None,
            "fecha_creacion": "2026-06-19 10:00:00",
            "requiere_devolucion": False,
            "monto_devolucion": 0,
            "estado_devolucion": "no_aplica"
        }
    ]

    with pytest.raises(HTTPException) as error:
        validar_superposicion_reserva(
            reservas=reservas,
            reserva_id_actual=None,
            cancha_id=1,
            fecha_reserva="2026-12-20",
            hora_inicio=time(10, 30),
            hora_fin=time(11, 30)
        )

    assert error.value.status_code == 400
    assert error.value.detail == "La cancha ya tiene una reserva en ese rango horario"


def test_validar_superposicion_reserva_sin_conflicto():
    reservas = [
        {
            "id": 1,
            "usuario_id": 2,
            "cancha_id": 1,
            "fecha": "2026-12-20",
            "hora_inicio": "10:00:00",
            "hora_fin": "11:00:00",
            "estado_reserva": "confirmada",
            "estado_pago": "pagado",
            "activa": True,
            "pagada": True,
            "motivo_cancelacion": None,
            "fecha_creacion": "2026-06-19 10:00:00",
            "requiere_devolucion": False,
            "monto_devolucion": 0,
            "estado_devolucion": "no_aplica"
        }
    ]

    validar_superposicion_reserva(
        reservas=reservas,
        reserva_id_actual=None,
        cancha_id=1,
        fecha_reserva="2026-12-20",
        hora_inicio=time(12, 0),
        hora_fin=time(13, 0)
    )


def test_validar_pago_correcto():
    datos_pago = PagoReservaRequest(
        numero_tarjeta="4111111111111111",
        nombre_titular="Nicolas Maidana",
        vencimiento="12/30",
        codigo_seguridad="123"
    )

    validar_pago(datos_pago)


def test_validar_pago_numero_tarjeta_invalido():
    datos_pago = PagoReservaRequest(
        numero_tarjeta="123",
        nombre_titular="Nicolas Maidana",
        vencimiento="12/30",
        codigo_seguridad="123"
    )

    with pytest.raises(HTTPException) as error:
        validar_pago(datos_pago)

    assert error.value.status_code == 400
    assert error.value.detail == "El número de tarjeta debe tener 16 dígitos numéricos"


def test_validar_pago_titular_vacio():
    datos_pago = PagoReservaRequest(
        numero_tarjeta="4111111111111111",
        nombre_titular="",
        vencimiento="12/30",
        codigo_seguridad="123"
    )

    with pytest.raises(HTTPException) as error:
        validar_pago(datos_pago)

    assert error.value.status_code == 400
    assert error.value.detail == "Debe ingresar el nombre del titular"


def test_validar_pago_vencimiento_formato_invalido():
    datos_pago = PagoReservaRequest(
        numero_tarjeta="4111111111111111",
        nombre_titular="Nicolas Maidana",
        vencimiento="1230",
        codigo_seguridad="123"
    )

    with pytest.raises(HTTPException) as error:
        validar_pago(datos_pago)

    assert error.value.status_code == 400
    assert error.value.detail == "El vencimiento debe tener formato MM/AA"


def test_validar_pago_tarjeta_vencida():
    datos_pago = PagoReservaRequest(
        numero_tarjeta="4111111111111111",
        nombre_titular="Nicolas Maidana",
        vencimiento="01/20",
        codigo_seguridad="123"
    )

    with pytest.raises(HTTPException) as error:
        validar_pago(datos_pago)

    assert error.value.status_code == 400
    assert error.value.detail == "La tarjeta se encuentra vencida"


def test_validar_pago_codigo_seguridad_invalido():
    datos_pago = PagoReservaRequest(
        numero_tarjeta="4111111111111111",
        nombre_titular="Nicolas Maidana",
        vencimiento="12/30",
        codigo_seguridad="12"
    )

    with pytest.raises(HTTPException) as error:
        validar_pago(datos_pago)

    assert error.value.status_code == 400
    assert error.value.detail == "El código de seguridad debe tener 3 o 4 dígitos"