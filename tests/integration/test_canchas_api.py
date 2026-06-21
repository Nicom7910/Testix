def test_listar_canchas(client):
    response = client.get("/canchas/")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 3
    assert data[0]["nombre"] == "Cancha 1"


def test_obtener_cancha_por_id(client):
    response = client.get("/canchas/1")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 1
    assert data["nombre"] == "Cancha 1"
    assert data["activa"] is True


def test_obtener_cancha_inexistente(client):
    response = client.get("/canchas/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Cancha no encontrada"


def test_listar_canchas_disponibles_sin_filtro(client):
    response = client.get("/canchas/disponibles")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    ids_canchas = [cancha["id"] for cancha in data]

    assert 1 in ids_canchas
    assert 2 in ids_canchas
    assert 3 not in ids_canchas


def test_listar_canchas_disponibles_con_horario_libre(client):
    response = client.get(
        "/canchas/disponibles",
        params={
            "fecha": "2026-12-20",
            "hora_inicio": "12:00:00",
            "hora_fin": "13:00:00"
        }
    )

    assert response.status_code == 200

    data = response.json()

    ids_canchas = [cancha["id"] for cancha in data]

    assert 1 in ids_canchas
    assert 2 in ids_canchas


def test_listar_canchas_disponibles_con_horario_ocupado(client):
    response = client.get(
        "/canchas/disponibles",
        params={
            "fecha": "2026-12-20",
            "hora_inicio": "10:30:00",
            "hora_fin": "11:30:00"
        }
    )

    assert response.status_code == 200

    data = response.json()

    ids_canchas = [cancha["id"] for cancha in data]

    assert 1 not in ids_canchas
    assert 2 in ids_canchas


def test_crear_cancha_como_admin(client):
    response = client.post(
        "/canchas/?admin_id=1",
        json={
            "nombre": "Cancha Nueva",
            "tipo_superficie": "Césped sintético",
            "techada": False,
            "precio_por_hora": 35000,
            "precio_diurno": 35000,
            "precio_nocturno": 42000
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["nombre"] == "Cancha Nueva"
    assert data["tipo_superficie"] == "Césped sintético"
    assert data["precio_por_hora"] == 35000
    assert data["activa"] is True


def test_crear_cancha_sin_ser_admin(client):
    response = client.post(
        "/canchas/?admin_id=2",
        json={
            "nombre": "Cancha No Permitida",
            "tipo_superficie": "Cemento",
            "techada": True,
            "precio_por_hora": 30000,
            "precio_diurno": 30000,
            "precio_nocturno": 36000
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "No tiene permisos de administrador"


def test_crear_cancha_con_precio_invalido(client):
    response = client.post(
        "/canchas/?admin_id=1",
        json={
            "nombre": "Cancha Precio Malo",
            "tipo_superficie": "Cemento",
            "techada": True,
            "precio_por_hora": 0,
            "precio_diurno": 0,
            "precio_nocturno": 0
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "El precio por hora debe ser mayor a 0"


def test_modificar_cancha_como_admin(client):
    response = client.put(
        "/canchas/1?admin_id=1",
        json={
            "nombre": "Cancha 1 Modificada",
            "tipo_superficie": "Polvo de ladrillo premium",
            "techada": True,
            "precio_por_hora": 25000,
            "precio_diurno": 25000,
            "precio_nocturno": 30000,
            "activa": True
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["nombre"] == "Cancha 1 Modificada"
    assert data["techada"] is True
    assert data["precio_por_hora"] == 25000


def test_modificar_precio_cancha_como_admin(client):
    response = client.patch(
        "/canchas/1/precio",
        params={
            "admin_id": 1,
            "precio_por_hora": 28000,
            "precio_diurno": 28000,
            "precio_nocturno": 33600
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["mensaje"] == "Precios actualizados correctamente"
    assert data["cancha"]["precio_por_hora"] == 28000
    assert data["cancha"]["precio_diurno"] == 28000
    assert data["cancha"]["precio_nocturno"] == 33600


def test_modificar_precio_cancha_sin_ser_admin(client):
    response = client.patch(
        "/canchas/1/precio",
        params={
            "admin_id": 2,
            "precio_por_hora": 28000
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "No tiene permisos de administrador"


def test_dar_baja_cancha_como_admin(client):
    response = client.delete("/canchas/1?admin_id=1")

    assert response.status_code == 200

    data = response.json()

    assert data["mensaje"] == "Cancha dada de baja correctamente"
    assert data["cancha"]["activa"] is False


def test_dar_baja_cancha_sin_ser_admin(client):
    response = client.delete("/canchas/1?admin_id=2")

    assert response.status_code == 403
    assert response.json()["detail"] == "No tiene permisos de administrador"