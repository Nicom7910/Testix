from fastapi import APIRouter, HTTPException, Query
from datetime import date, datetime

from app.utils.file_manager import leer_archivo
from app.utils.logger import logger


router = APIRouter(
    prefix="/reportes",
    tags=["Reportes"]
)

RUTA_RESERVAS = "app/data/reservas.json"
RUTA_CANCHAS = "app/data/canchas.json"
RUTA_USUARIOS = "app/data/usuarios.json"

ROL_ADMINISTRADOR = "ADMINISTRADOR"

ESTADO_RESERVA_PENDIENTE = "pendiente"
ESTADO_RESERVA_CONFIRMADA = "confirmada"
ESTADO_RESERVA_CANCELADA = "cancelada"
ESTADO_RESERVA_FINALIZADA = "finalizada"

ESTADO_PAGO_PENDIENTE = "pendiente"
ESTADO_PAGO_PAGADO = "pagado"
ESTADO_PAGO_RECHAZADO = "rechazado"


def validar_administrador(admin_id: int):
    logger.info(f"Validando administrador para reportes | admin_id={admin_id}")

    usuarios = leer_archivo(RUTA_USUARIOS)

    for usuario in usuarios:
        if usuario["id"] == admin_id:
            if usuario.get("activo", True) != True:
                logger.warning(
                    f"Reporte rechazado: administrador dado de baja | admin_id={admin_id}"
                )
                raise HTTPException(
                    status_code=403,
                    detail="El usuario administrador está dado de baja"
                )

            if usuario.get("rol") != ROL_ADMINISTRADOR:
                logger.warning(
                    f"Reporte rechazado: usuario sin permisos administrativos | usuario_id={admin_id} | rol={usuario.get('rol')}"
                )
                raise HTTPException(
                    status_code=403,
                    detail="No tiene permisos de administrador"
                )

            logger.info(f"Administrador validado para reportes | admin_id={admin_id}")
            return usuario

    logger.warning(f"Reporte rechazado: administrador no encontrado | admin_id={admin_id}")
    raise HTTPException(
        status_code=404,
        detail="Administrador no encontrado"
    )


def convertir_hora(texto_hora: str):
    try:
        return datetime.strptime(texto_hora, "%H:%M:%S").time()
    except ValueError:
        return datetime.strptime(texto_hora, "%H:%M").time()


def calcular_cantidad_horas(hora_inicio: str, hora_fin: str):
    inicio = convertir_hora(hora_inicio)
    fin = convertir_hora(hora_fin)

    fecha_base = date.today()

    inicio_datetime = datetime.combine(fecha_base, inicio)
    fin_datetime = datetime.combine(fecha_base, fin)

    if fin <= inicio:
        fin_datetime = fin_datetime.replace(day=fin_datetime.day + 1)

    diferencia = fin_datetime - inicio_datetime

    return diferencia.total_seconds() / 3600


def obtener_nombre_cancha(cancha_id: int, canchas: list):
    for cancha in canchas:
        if cancha["id"] == cancha_id:
            return cancha["nombre"]

    logger.warning(f"Reporte: cancha no encontrada al armar detalle | cancha_id={cancha_id}")
    return f"Cancha {cancha_id}"


def obtener_cliente(usuario_id: int, usuarios: list):
    for usuario in usuarios:
        if usuario["id"] == usuario_id:
            nombre = usuario.get("nombre", "")
            apellido = usuario.get("apellido", "")
            email = usuario.get("email", "")

            nombre_completo = f"{nombre} {apellido}".strip()

            if nombre_completo == "":
                return email

            return nombre_completo

    logger.warning(f"Reporte: usuario no encontrado al armar detalle | usuario_id={usuario_id}")
    return f"Usuario {usuario_id}"


def normalizar_reserva(reserva: dict):
    if "estado_reserva" not in reserva:
        if reserva.get("activa") == True:
            reserva["estado_reserva"] = ESTADO_RESERVA_CONFIRMADA
        elif reserva.get("motivo_cancelacion") is not None:
            reserva["estado_reserva"] = ESTADO_RESERVA_CANCELADA
        else:
            reserva["estado_reserva"] = ESTADO_RESERVA_PENDIENTE

    if "estado_pago" not in reserva:
        if reserva.get("pagada") == True:
            reserva["estado_pago"] = ESTADO_PAGO_PAGADO
        else:
            reserva["estado_pago"] = ESTADO_PAGO_PENDIENTE

    if "requiere_devolucion" not in reserva:
        reserva["requiere_devolucion"] = False

    if "monto_devolucion" not in reserva:
        reserva["monto_devolucion"] = 0

    if "estado_devolucion" not in reserva:
        reserva["estado_devolucion"] = "no_aplica"

    return reserva


def filtrar_reservas_por_periodo(
    reservas: list,
    fecha_desde: date | None,
    fecha_hasta: date | None
):
    logger.info(
        f"Filtrando reservas para reporte | fecha_desde={fecha_desde} | fecha_hasta={fecha_hasta}"
    )

    reservas_filtradas = []

    for reserva in reservas:
        try:
            fecha_reserva = datetime.strptime(
                reserva["fecha"],
                "%Y-%m-%d"
            ).date()
        except Exception as error:
            logger.error(
                f"Reporte: reserva omitida por fecha invalida | reserva_id={reserva.get('id')} | fecha={reserva.get('fecha')} | error={str(error)}"
            )
            continue

        if fecha_desde is not None and fecha_reserva < fecha_desde:
            continue

        if fecha_hasta is not None and fecha_reserva > fecha_hasta:
            continue

        reservas_filtradas.append(reserva)

    logger.info(
        f"Filtro de reporte aplicado | reservas_filtradas={len(reservas_filtradas)}"
    )

    return reservas_filtradas


@router.get("/general")
def obtener_reporte_general(
    admin_id: int = Query(...),
    fecha_desde: date | None = Query(default=None),
    fecha_hasta: date | None = Query(default=None)
):
    logger.info(
        f"Solicitud de reporte general | admin_id={admin_id} | fecha_desde={fecha_desde} | fecha_hasta={fecha_hasta}"
    )

    validar_administrador(admin_id)

    if (
        fecha_desde is not None
        and fecha_hasta is not None
        and fecha_desde > fecha_hasta
    ):
        logger.warning(
            f"Reporte rechazado: fecha desde mayor a fecha hasta | admin_id={admin_id} | fecha_desde={fecha_desde} | fecha_hasta={fecha_hasta}"
        )
        raise HTTPException(
            status_code=400,
            detail="La fecha desde no puede ser mayor a la fecha hasta"
        )

    reservas = leer_archivo(RUTA_RESERVAS)
    canchas = leer_archivo(RUTA_CANCHAS)
    usuarios = leer_archivo(RUTA_USUARIOS)

    logger.info(
        f"Datos cargados para reporte | reservas={len(reservas)} | canchas={len(canchas)} | usuarios={len(usuarios)}"
    )

    reservas_normalizadas = []

    for reserva in reservas:
        reservas_normalizadas.append(normalizar_reserva(reserva))

    reservas_filtradas = filtrar_reservas_por_periodo(
        reservas_normalizadas,
        fecha_desde,
        fecha_hasta
    )

    total_reservas = len(reservas_filtradas)

    reservas_por_estado = {
        ESTADO_RESERVA_PENDIENTE: 0,
        ESTADO_RESERVA_CONFIRMADA: 0,
        ESTADO_RESERVA_CANCELADA: 0,
        ESTADO_RESERVA_FINALIZADA: 0
    }

    pagos_por_estado = {
        ESTADO_PAGO_PENDIENTE: 0,
        ESTADO_PAGO_PAGADO: 0,
        ESTADO_PAGO_RECHAZADO: 0
    }

    ingresos_estimados = 0
    ingresos_cobrados = 0
    ingresos_potenciales = 0

    senas_cobradas = 0
    senas_pendientes = 0

    monto_devoluciones_pendientes = 0

    ocupacion_por_cancha = {}
    horarios_solicitados = {}
    detalle_reservas = []

    reservas_ordenadas = sorted(
        reservas_filtradas,
        key=lambda r: (
            r.get("fecha", ""),
            r.get("hora_inicio", ""),
            r.get("id", 0)
        )
    )

    for reserva in reservas_ordenadas:
        estado_reserva = reserva["estado_reserva"]
        estado_pago = reserva["estado_pago"]

        cancha_nombre = obtener_nombre_cancha(
            reserva["cancha_id"],
            canchas
        )

        cliente = obtener_cliente(
            reserva["usuario_id"],
            usuarios
        )

        horario = f"{reserva['hora_inicio'][:5]} a {reserva['hora_fin'][:5]}"

        detalle_reservas.append(
            {
                "reserva_id": reserva["id"],
                "cancha": cancha_nombre,
                "fecha": reserva["fecha"],
                "horario": horario,
                "cliente": cliente,
                "estado_reserva": estado_reserva,
                "estado_pago": estado_pago,
                "monto_total": reserva.get("monto_total", 0),
                "seña": reserva.get("sena", 0)
            }
        )

        if estado_reserva in reservas_por_estado:
            reservas_por_estado[estado_reserva] += 1
        else:
            logger.warning(
                f"Reporte: estado de reserva desconocido | reserva_id={reserva.get('id')} | estado={estado_reserva}"
            )

        if estado_pago in pagos_por_estado:
            pagos_por_estado[estado_pago] += 1
        else:
            logger.warning(
                f"Reporte: estado de pago desconocido | reserva_id={reserva.get('id')} | estado_pago={estado_pago}"
            )

        reserva_cancelada = estado_reserva == ESTADO_RESERVA_CANCELADA
        reserva_pagada = estado_pago == ESTADO_PAGO_PAGADO
        reserva_pendiente = estado_reserva == ESTADO_RESERVA_PENDIENTE

        if not reserva_cancelada:
            ingresos_potenciales += reserva.get("monto_total", 0)

        if reserva_pagada and not reserva_cancelada:
            ingresos_estimados += reserva.get("monto_total", 0)
            ingresos_cobrados += reserva.get("sena", 0)
            senas_cobradas += reserva.get("sena", 0)

        if reserva_pendiente:
            senas_pendientes += reserva.get("sena", 0)

        if reserva.get("requiere_devolucion") == True:
            if reserva.get("estado_devolucion") == "pendiente":
                monto_devoluciones_pendientes += reserva.get(
                    "monto_devolucion",
                    0
                )

        if not reserva_cancelada:
            cancha_id = reserva["cancha_id"]

            if cancha_id not in ocupacion_por_cancha:
                ocupacion_por_cancha[cancha_id] = {
                    "cancha_id": cancha_id,
                    "cancha": cancha_nombre,
                    "cantidad_reservas": 0,
                    "horas_reservadas": 0,
                    "ingresos_estimados": 0
                }

            ocupacion_por_cancha[cancha_id]["cantidad_reservas"] += 1

            try:
                horas_reservadas = calcular_cantidad_horas(
                    reserva["hora_inicio"],
                    reserva["hora_fin"]
                )
            except Exception as error:
                logger.error(
                    f"Reporte: no se pudieron calcular horas | reserva_id={reserva.get('id')} | error={str(error)}"
                )
                horas_reservadas = reserva.get("cantidad_horas", 0)

            ocupacion_por_cancha[cancha_id]["horas_reservadas"] += horas_reservadas

            if reserva_pagada:
                ocupacion_por_cancha[cancha_id]["ingresos_estimados"] += reserva.get(
                    "monto_total",
                    0
                )

            hora_inicio = reserva["hora_inicio"][:5]

            if hora_inicio not in horarios_solicitados:
                horarios_solicitados[hora_inicio] = {
                    "hora_inicio": hora_inicio,
                    "cantidad_reservas": 0
                }

            horarios_solicitados[hora_inicio]["cantidad_reservas"] += 1

    ocupacion_lista = list(ocupacion_por_cancha.values())
    ocupacion_lista.sort(
        key=lambda item: item["cantidad_reservas"],
        reverse=True
    )

    horarios_lista = list(horarios_solicitados.values())
    horarios_lista.sort(
        key=lambda item: item["cantidad_reservas"],
        reverse=True
    )

    reservas_no_canceladas = (
        reservas_por_estado[ESTADO_RESERVA_PENDIENTE]
        + reservas_por_estado[ESTADO_RESERVA_CONFIRMADA]
        + reservas_por_estado[ESTADO_RESERVA_FINALIZADA]
    )

    porcentaje_cancelacion = 0

    if total_reservas > 0:
        porcentaje_cancelacion = (
            reservas_por_estado[ESTADO_RESERVA_CANCELADA] / total_reservas
        ) * 100

    logger.info(
        f"Reporte general generado correctamente | admin_id={admin_id} | total_reservas={total_reservas} | ingresos_cobrados={round(ingresos_cobrados, 2)} | porcentaje_cancelacion={round(porcentaje_cancelacion, 2)}"
    )

    return {
        "periodo": {
            "fecha_desde": str(fecha_desde) if fecha_desde is not None else None,
            "fecha_hasta": str(fecha_hasta) if fecha_hasta is not None else None
        },
        "resumen": {
            "total_reservas": total_reservas,
            "reservas_no_canceladas": reservas_no_canceladas,
            "reservas_canceladas": reservas_por_estado[ESTADO_RESERVA_CANCELADA],
            "reservas_pendientes": reservas_por_estado[ESTADO_RESERVA_PENDIENTE],
            "porcentaje_cancelacion": round(porcentaje_cancelacion, 2),
            "ingresos_estimados": round(ingresos_estimados, 2),
            "ingresos_cobrados": round(ingresos_cobrados, 2),
            "ingresos_potenciales": round(ingresos_potenciales, 2),
            "senas_cobradas": round(senas_cobradas, 2),
            "senas_pendientes": round(senas_pendientes, 2),
            "devoluciones_pendientes": round(monto_devoluciones_pendientes, 2)
        },
        "reservas_por_estado": reservas_por_estado,
        "pagos_por_estado": pagos_por_estado,
        "detalle_reservas": detalle_reservas,
        "ocupacion_por_cancha": ocupacion_lista,
        "horarios_mas_solicitados": horarios_lista
    }