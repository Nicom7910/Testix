def test_login_usuario_correcto(client):
    response = client.post(
        "/usuarios/login",
        json={
            "email": "nico@test.com",
            "password": "cliente123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["mensaje"] == "Login exitoso"
    assert data["usuario"]["email"] == "nico@test.com"
    assert data["usuario"]["rol"] == "COMUN"


def test_login_usuario_incorrecto(client):
    response = client.post(
        "/usuarios/login",
        json={
            "email": "nico@test.com",
            "password": "password_incorrecta"
        }
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Email o contraseña incorrectos"


def test_registro_usuario_correcto(client):
    response = client.post(
        "/usuarios/",
        json={
            "nombre": "Juan",
            "apellido": "Perez",
            "email": "juan@test.com",
            "telefono": "4444444444",
            "password": "juan123",
            "rol": "COMUN"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["nombre"] == "Juan"
    assert data["apellido"] == "Perez"
    assert data["email"] == "juan@test.com"
    assert data["rol"] == "COMUN"
    assert data["activo"] is True


def test_registro_usuario_email_repetido(client):
    response = client.post(
        "/usuarios/",
        json={
            "nombre": "Nico",
            "apellido": "Repetido",
            "email": "nico@test.com",
            "telefono": "5555555555",
            "password": "otro123",
            "rol": "COMUN"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Ya existe un usuario con ese email"


def test_listar_usuarios_como_admin(client):
    response = client.get("/usuarios/?admin_id=1")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 3


def test_listar_usuarios_sin_ser_admin(client):
    response = client.get("/usuarios/?admin_id=2")

    assert response.status_code == 403
    assert response.json()["detail"] == "No tiene permisos de administrador"


def test_obtener_usuario_propio(client):
    response = client.get("/usuarios/2?usuario_id_solicitante=2")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 2
    assert data["email"] == "nico@test.com"


def test_obtener_otro_usuario_sin_permiso(client):
    response = client.get("/usuarios/1?usuario_id_solicitante=2")

    assert response.status_code == 403
    assert response.json()["detail"] == "No tiene permisos para consultar este usuario"


def test_modificar_usuario_propio(client):
    response = client.put(
        "/usuarios/2?usuario_id_solicitante=2",
        json={
            "nombre": "Nicolas Modificado",
            "apellido": "Cliente",
            "email": "nico.modificado@test.com",
            "telefono": "9999999999",
            "password": "cliente123",
            "rol": "COMUN",
            "activo": True
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["nombre"] == "Nicolas Modificado"
    assert data["email"] == "nico.modificado@test.com"


def test_dar_baja_usuario_como_admin(client):
    response = client.delete("/usuarios/2?admin_id=1")

    assert response.status_code == 200

    data = response.json()

    assert data["mensaje"] == "Usuario dado de baja correctamente"
    assert data["usuario"]["activo"] is False


def test_dar_baja_usuario_sin_ser_admin(client):
    response = client.delete("/usuarios/1?admin_id=2")

    assert response.status_code == 403
    assert response.json()["detail"] == "No tiene permisos de administrador"