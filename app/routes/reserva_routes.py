from fastapi import APIRouter, HTTPException
from datetime import datetime

from app.schemas.reserva_schema import (
    ReservaCreate,
    ReservaResponse,
    CancelarReservaRequest,
    PagoReservaRequest
)
from app.utils.file_manager import leer_archivo, guardar_archivo, obtener_siguiente_id

router = APIRouter(
    prefix="/reservas",
    tags=["Reservas"]
)

RUTA_RESERVAS = "app/data/reservas.json"
RUTA_CANCHAS = "app/data/canchas.json"
RUTA_USUARIOS = "app/data/usuarios.json"


@router.post("/", response_model=ReservaResponse)
def crear_reserva(reserva: ReservaCreate):
    reservas = leer_archivo(RUTA_RESERVAS)
    canchas = leer_archivo(RUTA_CANCHAS)
    usuarios = leer_archivo(RUTA_USUARIOS)

    usuario_encontrado = None

    for usuario in usuarios:
        if usuario["id"] == reserva.usuario_id and usuario["activo"] == True:
            usuario_encontrado = usuario

    if usuario_encontrado is None:
        raise HTTPException(
            status_code=404,
            detail="El usuario no existe o está dado de baja"
        )

    cancha_encontrada = None

    for cancha in canchas:
        if cancha["id"] == reserva.cancha_id and cancha["activa"] == True:
            cancha_encontrada = cancha

    if cancha_encontrada is None:
        raise HTTPException(
            status_code=404,
            detail="La cancha no existe o no está disponible"
        )

    hora_inicio = reserva.hora_inicio
    hora_fin = reserva.hora_fin

    if hora_fin <= hora_inicio:
        raise HTTPException(
            status_code=400,
            detail="La hora de fin debe ser mayor a la hora de inicio"
        )

    inicio_datetime = datetime.combine(reserva.fecha, hora_inicio)
    fin_datetime = datetime.combine(reserva.fecha, hora_fin)

    diferencia = fin_datetime - inicio_datetime
    cantidad_horas = diferencia.total_seconds() / 3600

    for r in reservas:
        if (
            r["cancha_id"] == reserva.cancha_id
            and r["fecha"] == str(reserva.fecha)
            and r["activa"] == True
        ):

            if "hora_inicio" not in r or "hora_fin" not in r:
                continue

            reserva_inicio_existente = datetime.strptime(
                r["hora_inicio"],
                "%H:%M:%S"
            ).time()

            reserva_fin_existente = datetime.strptime(
                r["hora_fin"],
                "%H:%M:%S"
            ).time()

            hay_superposicion = (
                hora_inicio < reserva_fin_existente
                and hora_fin > reserva_inicio_existente
            )

            if hay_superposicion:
                raise HTTPException(
                    status_code=400,
                    detail="La cancha ya está reservada en ese rango horario"
                )

    precio_por_hora = cancha_encontrada["precio_por_hora"]
    monto_total = precio_por_hora * cantidad_horas
    sena = monto_total * 0.5

    nueva_reserva = {
        "id": obtener_siguiente_id(reservas),
        "usuario_id": reserva.usuario_id,
        "cancha_id": reserva.cancha_id,
        "fecha": str(reserva.fecha),
        "hora_inicio": hora_inicio.strftime("%H:%M:%S"),
        "hora_fin": hora_fin.strftime("%H:%M:%S"),
        "cantidad_horas": cantidad_horas,
        "monto_total": monto_total,
        "sena": sena,
        "activa": False,
        "pagada": False,
        "motivo_cancelacion": None
    }

    reservas.append(nueva_reserva)
    guardar_archivo(RUTA_RESERVAS, reservas)

    return nueva_reserva


@router.get("/", response_model=list[ReservaResponse])
def listar_reservas():
    reservas = leer_archivo(RUTA_RESERVAS)
    return reservas


@router.get("/activas", response_model=list[ReservaResponse])
def listar_reservas_activas():
    reservas = leer_archivo(RUTA_RESERVAS)

    reservas_activas = []

    for reserva in reservas:
        if reserva["activa"] == True:
            reservas_activas.append(reserva)

    return reservas_activas


@router.get("/usuario/{usuario_id}/activas", response_model=list[ReservaResponse])
def listar_reservas_activas_usuario(usuario_id: int):
    reservas = leer_archivo(RUTA_RESERVAS)

    reservas_usuario = []

    for reserva in reservas:
        if reserva["usuario_id"] == usuario_id and reserva["activa"] == True:
            reservas_usuario.append(reserva)

    return reservas_usuario


@router.put("/{reserva_id}/pagar", response_model=ReservaResponse)
def pagar_sena_reserva(
    reserva_id: int,
    datos_pago: PagoReservaRequest
):
    reservas = leer_archivo(RUTA_RESERVAS)

    if (
        datos_pago.numero_tarjeta.strip() == ""
        or datos_pago.nombre_titular.strip() == ""
        or datos_pago.vencimiento.strip() == ""
        or datos_pago.codigo_seguridad.strip() == ""
    ):
        raise HTTPException(
            status_code=400,
            detail="Debe completar todos los datos de pago"
        )

    for reserva in reservas:
        if reserva["id"] == reserva_id:

            if reserva["pagada"] == True:
                raise HTTPException(
                    status_code=400,
                    detail="La reserva ya fue pagada"
                )

            reserva["pagada"] = True
            reserva["activa"] = True

            guardar_archivo(RUTA_RESERVAS, reservas)

            return reserva

    raise HTTPException(status_code=404, detail="Reserva no encontrada")


@router.put("/{reserva_id}/cancelar")
def cancelar_reserva(
    reserva_id: int,
    datos: CancelarReservaRequest
):
    reservas = leer_archivo(RUTA_RESERVAS)

    if datos.motivo_cancelacion.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="Debe ingresar un motivo de cancelación"
        )

    for reserva in reservas:
        if reserva["id"] == reserva_id:

            if reserva["activa"] == False and reserva["pagada"] == True:
                raise HTTPException(
                    status_code=400,
                    detail="La reserva ya se encuentra cancelada"
                )

            reserva["activa"] = False
            reserva["motivo_cancelacion"] = datos.motivo_cancelacion

            guardar_archivo(RUTA_RESERVAS, reservas)

            return {
                "mensaje": "Reserva cancelada correctamente",
                "reserva": reserva
            }

    raise HTTPException(status_code=404, detail="Reserva no encontrada")