from datetime import date, timedelta


def test_listar_reservas_como_admin(client):
    response = client.get("/reservas/?admin_id=1")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 2


def test_listar_reservas_sin_ser_admin(client):
    response = client.get("/reservas/?admin_id=2")

    assert response.status_code == 403
    assert response.json()["detail"] == "No tiene permisos de administrador"


def test_listar_reservas_activas_usuario(client):
    response = client.get("/reservas/usuario/2/activas")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["estado_reserva"] == "confirmada"


def test_listar_reservas_pendientes_usuario(client):
    response = client.get("/reservas/usuario/2/pendientes")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["estado_reserva"] == "pendiente"


def test_listar_historial_usuario(client):
    response = client.get("/reservas/usuario/2/historial")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 2


def test_crear_reserva_correcta(client):
    response = client.post(
        "/reservas/",
        json={
            "usuario_id": 2,
            "cancha_id": 2,
            "fecha": "2026-12-20",
            "hora_inicio": "12:00:00",
            "hora_fin": "13:30:00"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["usuario_id"] == 2
    assert data["cancha_id"] == 2
    assert data["fecha"] == "2026-12-20"
    assert data["hora_inicio"] == "12:00:00"
    assert data["hora_fin"] == "13:30:00"
    assert data["cantidad_horas"] == 1.5
    assert data["estado_reserva"] == "pendiente"
    assert data["estado_pago"] == "pendiente"
    assert data["activa"] is False
    assert data["pagada"] is False


def test_crear_reserva_usuario_inexistente(client):
    response = client.post(
        "/reservas/",
        json={
            "usuario_id": 999,
            "cancha_id": 1,
            "fecha": "2026-12-20",
            "hora_inicio": "12:00:00",
            "hora_fin": "13:00:00"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "El usuario no existe o está dado de baja"


def test_crear_reserva_cancha_inexistente(client):
    response = client.post(
        "/reservas/",
        json={
            "usuario_id": 2,
            "cancha_id": 999,
            "fecha": "2026-12-20",
            "hora_inicio": "12:00:00",
            "hora_fin": "13:00:00"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "La cancha no existe"


def test_crear_reserva_cancha_deshabilitada(client):
    response = client.post(
        "/reservas/",
        json={
            "usuario_id": 2,
            "cancha_id": 3,
            "fecha": "2026-12-20",
            "hora_inicio": "12:00:00",
            "hora_fin": "13:00:00"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "La cancha seleccionada está deshabilitada"


def test_crear_reserva_superpuesta(client):
    response = client.post(
        "/reservas/",
        json={
            "usuario_id": 2,
            "cancha_id": 1,
            "fecha": "2026-12-20",
            "hora_inicio": "10:30:00",
            "hora_fin": "11:30:00"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "La cancha ya tiene una reserva en ese rango horario"


def test_crear_reserva_fecha_pasada(client):
    fecha_pasada = date.today() - timedelta(days=1)

    response = client.post(
        "/reservas/",
        json={
            "usuario_id": 2,
            "cancha_id": 1,
            "fecha": str(fecha_pasada),
            "hora_inicio": "10:00:00",
            "hora_fin": "11:00:00"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "No se pueden crear reservas con fecha anterior a la actual"


def test_crear_reserva_hora_inicio_mayor_igual_fin(client):
    response = client.post(
        "/reservas/",
        json={
            "usuario_id": 2,
            "cancha_id": 1,
            "fecha": "2026-12-20",
            "hora_inicio": "14:00:00",
            "hora_fin": "14:00:00"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "La hora de fin debe ser mayor a la hora de inicio, excepto si finaliza a las 00:00"


def test_pagar_sena_correctamente(client):
    response = client.put(
        "/reservas/2/pagar",
        json={
            "numero_tarjeta": "4111111111111111",
            "nombre_titular": "Nicolas Maidana",
            "vencimiento": "12/30",
            "codigo_seguridad": "123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 2
    assert data["estado_pago"] == "pagado"
    assert data["estado_reserva"] == "confirmada"
    assert data["pagada"] is True
    assert data["activa"] is True


def test_pagar_sena_tarjeta_invalida(client):
    response = client.put(
        "/reservas/2/pagar",
        json={
            "numero_tarjeta": "123",
            "nombre_titular": "Nicolas Maidana",
            "vencimiento": "12/30",
            "codigo_seguridad": "123"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "El número de tarjeta debe tener 16 dígitos numéricos"


def test_pagar_sena_tarjeta_vencida(client):
    response = client.put(
        "/reservas/2/pagar",
        json={
            "numero_tarjeta": "4111111111111111",
            "nombre_titular": "Nicolas Maidana",
            "vencimiento": "01/20",
            "codigo_seguridad": "123"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "La tarjeta se encuentra vencida"


def test_pagar_sena_rechazada_por_simulacion(client):
    response = client.put(
        "/reservas/2/pagar",
        json={
            "numero_tarjeta": "0000111122223333",
            "nombre_titular": "Nicolas Maidana",
            "vencimiento": "12/30",
            "codigo_seguridad": "123"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "El pago fue rechazado"


def test_cancelar_reserva_con_motivo(client):
    response = client.put(
        "/reservas/2/cancelar?usuario_id_solicitante=2",
        json={
            "motivo_cancelacion": "No puedo asistir al turno"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "Reserva cancelada correctamente" in data["mensaje"]
    assert data["reserva"]["estado_reserva"] == "cancelada"
    assert data["reserva"]["activa"] is False
    assert data["reserva"]["motivo_cancelacion"] == "No puedo asistir al turno"


def test_cancelar_reserva_sin_motivo(client):
    response = client.put(
        "/reservas/2/cancelar?usuario_id_solicitante=2",
        json={
            "motivo_cancelacion": ""
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Debe ingresar un motivo de cancelación"


def test_cancelar_reserva_de_otro_usuario_sin_permiso(client):
    response = client.put(
        "/reservas/1/cancelar?usuario_id_solicitante=3",
        json={
            "motivo_cancelacion": "Intento cancelar una reserva ajena"
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "El usuario está dado de baja"