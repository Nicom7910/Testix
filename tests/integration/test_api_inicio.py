def test_inicio_api(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["mensaje"] == "API del Sistema de Gestión de Alquiler de Canchas de Tenis"