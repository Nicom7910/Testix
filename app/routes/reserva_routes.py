from fastapi import APIRouter, HTTPException

from app.schemas.reserva_schema import ReservaCreate, ReservaResponse
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

    for r in reservas:
        if (
            r["cancha_id"] == reserva.cancha_id
            and r["fecha"] == str(reserva.fecha)
            and r["hora"] == reserva.hora.strftime("%H:%M:%S")
            and r["activa"] == True
        ):
            raise HTTPException(
                status_code=400,
                detail="La cancha ya está reservada para ese día y horario"
            )

    monto_total = cancha_encontrada["precio_por_hora"]
    sena = monto_total * 0.5

    nueva_reserva = {
        "id": obtener_siguiente_id(reservas),
        "usuario_id": reserva.usuario_id,
        "cancha_id": reserva.cancha_id,
        "fecha": str(reserva.fecha),
        "hora": reserva.hora.strftime("%H:%M:%S"),
        "monto_total": monto_total,
        "sena": sena,
        "activa": True
    }

    reservas.append(nueva_reserva)
    guardar_archivo(RUTA_RESERVAS, reservas)

    return nueva_reserva


@router.get("/", response_model=list[ReservaResponse])
def listar_reservas():
    reservas = leer_archivo(RUTA_RESERVAS)
    return reservas


@router.get("/usuario/{usuario_id}/activas", response_model=list[ReservaResponse])
def listar_reservas_activas_usuario(usuario_id: int):
    reservas = leer_archivo(RUTA_RESERVAS)

    reservas_usuario = []

    for reserva in reservas:
        if reserva["usuario_id"] == usuario_id and reserva["activa"] == True:
            reservas_usuario.append(reserva)

    return reservas_usuario


@router.delete("/{reserva_id}")
def cancelar_reserva(reserva_id: int):
    reservas = leer_archivo(RUTA_RESERVAS)

    for reserva in reservas:
        if reserva["id"] == reserva_id:
            reserva["activa"] = False
            guardar_archivo(RUTA_RESERVAS, reservas)

            return {
                "mensaje": "Reserva cancelada correctamente",
                "reserva": reserva
            }

    raise HTTPException(status_code=404, detail="Reserva no encontrada")