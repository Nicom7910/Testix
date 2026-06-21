def test_reporte_general_como_admin(client):
    response = client.get("/reportes/general?admin_id=1")

    assert response.status_code == 200

    data = response.json()

    assert "periodo" in data
    assert "resumen" in data
    assert "reservas_por_estado" in data
    assert "pagos_por_estado" in data
    assert "detalle_reservas" in data
    assert "ocupacion_por_cancha" in data
    assert "horarios_mas_solicitados" in data

    assert data["resumen"]["total_reservas"] >= 2
    assert "pendiente" in data["reservas_por_estado"]
    assert "confirmada" in data["reservas_por_estado"]
    assert "cancelada" in data["reservas_por_estado"]
    assert "finalizada" in data["reservas_por_estado"]


def test_reporte_general_sin_ser_admin(client):
    response = client.get("/reportes/general?admin_id=2")

    assert response.status_code == 403
    assert response.json()["detail"] == "No tiene permisos de administrador"


def test_reporte_general_admin_inexistente(client):
    response = client.get("/reportes/general?admin_id=999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Administrador no encontrado"


def test_reporte_general_con_filtro_de_fechas(client):
    response = client.get(
        "/reportes/general",
        params={
            "admin_id": 1,
            "fecha_desde": "2026-12-20",
            "fecha_hasta": "2026-12-21"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["periodo"]["fecha_desde"] == "2026-12-20"
    assert data["periodo"]["fecha_hasta"] == "2026-12-21"
    assert data["resumen"]["total_reservas"] >= 2


def test_reporte_general_con_fecha_desde_mayor_a_fecha_hasta(client):
    response = client.get(
        "/reportes/general",
        params={
            "admin_id": 1,
            "fecha_desde": "2026-12-31",
            "fecha_hasta": "2026-12-01"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "La fecha desde no puede ser mayor a la fecha hasta"


def test_reporte_general_sin_reservas_en_periodo(client):
    response = client.get(
        "/reportes/general",
        params={
            "admin_id": 1,
            "fecha_desde": "2030-01-01",
            "fecha_hasta": "2030-01-31"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["resumen"]["total_reservas"] == 0
    assert data["resumen"]["reservas_no_canceladas"] == 0
    assert data["resumen"]["reservas_canceladas"] == 0
    assert data["detalle_reservas"] == []
    assert data["ocupacion_por_cancha"] == []
    assert data["horarios_mas_solicitados"] == []


def test_reporte_general_calcula_ingresos_y_senas(client):
    response = client.get("/reportes/general?admin_id=1")

    assert response.status_code == 200

    data = response.json()
    resumen = data["resumen"]

    assert resumen["ingresos_estimados"] >= 20000
    assert resumen["ingresos_cobrados"] >= 10000
    assert resumen["senas_cobradas"] >= 10000
    assert resumen["senas_pendientes"] >= 15000


def test_reporte_general_incluye_ocupacion_por_cancha(client):
    response = client.get("/reportes/general?admin_id=1")

    assert response.status_code == 200

    data = response.json()

    ocupacion = data["ocupacion_por_cancha"]

    assert isinstance(ocupacion, list)
    assert len(ocupacion) >= 1

    primera_cancha = ocupacion[0]

    assert "cancha_id" in primera_cancha
    assert "cancha" in primera_cancha
    assert "cantidad_reservas" in primera_cancha
    assert "horas_reservadas" in primera_cancha
    assert "ingresos_estimados" in primera_cancha


def test_reporte_general_incluye_detalle_reservas(client):
    response = client.get("/reportes/general?admin_id=1")

    assert response.status_code == 200

    data = response.json()

    detalle = data["detalle_reservas"]

    assert isinstance(detalle, list)
    assert len(detalle) >= 2

    primera_reserva = detalle[0]

    assert "reserva_id" in primera_reserva
    assert "cancha" in primera_reserva
    assert "fecha" in primera_reserva
    assert "horario" in primera_reserva
    assert "cliente" in primera_reserva
    assert "estado_reserva" in primera_reserva
    assert "estado_pago" in primera_reserva
    assert "monto_total" in primera_reserva
    assert "seña" in primera_reserva