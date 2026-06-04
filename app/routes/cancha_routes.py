from fastapi import APIRouter, HTTPException, Query
from datetime import date, time, datetime, timedelta

from app.schemas.cancha_schema import CanchaCreate, CanchaUpdate, CanchaResponse
from app.utils.file_manager import leer_archivo, guardar_archivo, obtener_siguiente_id

router = APIRouter(
    prefix="/canchas",
    tags=["Canchas"]
)

RUTA_CANCHAS = "app/data/canchas.json"
RUTA_RESERVAS = "app/data/reservas.json"
RUTA_USUARIOS = "app/data/usuarios.json"

ROL_ADMINISTRADOR = "ADMINISTRADOR"

ESTADO_RESERVA_PENDIENTE = "pendiente"
ESTADO_RESERVA_CONFIRMADA = "confirmada"
ESTADO_RESERVA_CANCELADA = "cancelada"
ESTADO_RESERVA_FINALIZADA = "finalizada"

HORA_APERTURA = time(8, 0)
HORA_CIERRE = time(23, 0)
HORA_MEDIANOCHE = time(0, 0)


def validar_administrador(admin_id: int):
    usuarios = leer_archivo(RUTA_USUARIOS)

    for usuario in usuarios:
        if usuario["id"] == admin_id:
            if usuario.get("activo", True) != True:
                raise HTTPException(
                    status_code=403,
                    detail="El usuario administrador está dado de baja"
                )

            if usuario.get("rol") != ROL_ADMINISTRADOR:
                raise HTTPException(
                    status_code=403,
                    detail="No tiene permisos de administrador"
                )

            return usuario

    raise HTTPException(
        status_code=404,
        detail="Administrador no encontrado"
    )


def convertir_hora(texto_hora: str):
    try:
        return datetime.strptime(texto_hora, "%H:%M:%S").time()
    except ValueError:
        return datetime.strptime(texto_hora, "%H:%M").time()


def obtener_estado_reserva(reserva: dict):
    if "estado_reserva" in reserva:
        return reserva["estado_reserva"]

    if reserva.get("activa") == True:
        return ESTADO_RESERVA_CONFIRMADA

    if reserva.get("motivo_cancelacion") is not None:
        return ESTADO_RESERVA_CANCELADA

    return ESTADO_RESERVA_PENDIENTE


def normalizar_cancha(cancha: dict):
    if "precio_diurno" not in cancha or cancha["precio_diurno"] is None:
        cancha["precio_diurno"] = cancha["precio_por_hora"]

    if "precio_nocturno" not in cancha or cancha["precio_nocturno"] is None:
        cancha["precio_nocturno"] = round(cancha["precio_por_hora"] * 1.2, 2)

    return cancha


def normalizar_canchas(canchas: list):
    hubo_cambios = False

    for cancha in canchas:
        original = cancha.copy()
        normalizar_cancha(cancha)

        if cancha != original:
            hubo_cambios = True

    return hubo_cambios


def obtener_intervalo_datetime(fecha_reserva: date, hora_inicio: time, hora_fin: time):
    inicio = datetime.combine(fecha_reserva, hora_inicio)
    fin = datetime.combine(fecha_reserva, hora_fin)

    if hora_fin <= hora_inicio:
        fin = fin + timedelta(days=1)

    return inicio, fin


def validar_fecha_y_horario(fecha_reserva: date, hora_inicio: time, hora_fin: time):
    ahora = datetime.now()
    hoy = ahora.date()

    if fecha_reserva < hoy:
        raise HTTPException(
            status_code=400,
            detail="No se pueden consultar ni reservar fechas anteriores a la actual"
        )

    if hora_inicio < HORA_APERTURA or hora_inicio > HORA_CIERRE:
        raise HTTPException(
            status_code=400,
            detail="La hora de inicio debe estar entre 08:00 y 23:00"
        )

    if hora_fin != HORA_MEDIANOCHE:
        if hora_fin <= hora_inicio:
            raise HTTPException(
                status_code=400,
                detail="La hora de fin debe ser mayor a la hora de inicio, excepto si finaliza a las 00:00"
            )

        if hora_fin > HORA_CIERRE:
            raise HTTPException(
                status_code=400,
                detail="La hora de fin debe ser hasta las 23:00 o 00:00"
            )

    inicio_reserva, _ = obtener_intervalo_datetime(
        fecha_reserva,
        hora_inicio,
        hora_fin
    )

    if inicio_reserva <= ahora:
        raise HTTPException(
            status_code=400,
            detail="No se pueden consultar ni reservar horarios anteriores al momento actual"
        )


def hay_superposicion(
    inicio_nuevo: datetime,
    fin_nuevo: datetime,
    inicio_existente: datetime,
    fin_existente: datetime
) -> bool:
    return inicio_nuevo < fin_existente and fin_nuevo > inicio_existente


@router.post("/", response_model=CanchaResponse)
def crear_cancha(
    cancha: CanchaCreate,
    admin_id: int = Query(...)
):
    validar_administrador(admin_id)

    canchas = leer_archivo(RUTA_CANCHAS)

    if cancha.precio_por_hora <= 0:
        raise HTTPException(
            status_code=400,
            detail="El precio por hora debe ser mayor a 0"
        )

    precio_diurno = cancha.precio_diurno
    precio_nocturno = cancha.precio_nocturno

    if precio_diurno is None:
        precio_diurno = cancha.precio_por_hora

    if precio_nocturno is None:
        precio_nocturno = round(cancha.precio_por_hora * 1.2, 2)

    if precio_diurno <= 0 or precio_nocturno <= 0:
        raise HTTPException(
            status_code=400,
            detail="Los precios diurno y nocturno deben ser mayores a 0"
        )

    nueva_cancha = {
        "id": obtener_siguiente_id(canchas),
        "nombre": cancha.nombre,
        "tipo_superficie": cancha.tipo_superficie,
        "techada": cancha.techada,
        "precio_por_hora": cancha.precio_por_hora,
        "precio_diurno": precio_diurno,
        "precio_nocturno": precio_nocturno,
        "activa": True
    }

    canchas.append(nueva_cancha)
    guardar_archivo(RUTA_CANCHAS, canchas)

    return nueva_cancha


@router.get("/", response_model=list[CanchaResponse])
def listar_canchas():
    canchas = leer_archivo(RUTA_CANCHAS)

    if normalizar_canchas(canchas):
        guardar_archivo(RUTA_CANCHAS, canchas)

    return canchas


@router.get("/disponibles", response_model=list[CanchaResponse])
def listar_canchas_disponibles(
    fecha: date | None = Query(default=None),
    hora_inicio: time | None = Query(default=None),
    hora_fin: time | None = Query(default=None)
):
    canchas = leer_archivo(RUTA_CANCHAS)
    reservas = leer_archivo(RUTA_RESERVAS)

    if normalizar_canchas(canchas):
        guardar_archivo(RUTA_CANCHAS, canchas)

    if fecha is None or hora_inicio is None or hora_fin is None:
        return [cancha for cancha in canchas if cancha["activa"] == True]

    validar_fecha_y_horario(fecha, hora_inicio, hora_fin)

    inicio_nuevo, fin_nuevo = obtener_intervalo_datetime(
        fecha,
        hora_inicio,
        hora_fin
    )

    disponibles = []

    for cancha in canchas:
        if cancha["activa"] != True:
            continue

        cancha_ocupada = False

        for reserva in reservas:
            estado_reserva = obtener_estado_reserva(reserva)

            if estado_reserva not in [
                ESTADO_RESERVA_PENDIENTE,
                ESTADO_RESERVA_CONFIRMADA
            ]:
                continue

            if (
                reserva["cancha_id"] == cancha["id"]
                and reserva["fecha"] == str(fecha)
            ):
                reserva_inicio = convertir_hora(reserva["hora_inicio"])
                reserva_fin = convertir_hora(reserva["hora_fin"])

                inicio_existente, fin_existente = obtener_intervalo_datetime(
                    fecha,
                    reserva_inicio,
                    reserva_fin
                )

                if hay_superposicion(
                    inicio_nuevo,
                    fin_nuevo,
                    inicio_existente,
                    fin_existente
                ):
                    cancha_ocupada = True
                    break

        if cancha_ocupada == False:
            disponibles.append(cancha)

    return disponibles


@router.get("/{cancha_id}", response_model=CanchaResponse)
def obtener_cancha(cancha_id: int):
    canchas = leer_archivo(RUTA_CANCHAS)

    if normalizar_canchas(canchas):
        guardar_archivo(RUTA_CANCHAS, canchas)

    for cancha in canchas:
        if cancha["id"] == cancha_id:
            return cancha

    raise HTTPException(status_code=404, detail="Cancha no encontrada")


@router.put("/{cancha_id}", response_model=CanchaResponse)
def modificar_cancha(
    cancha_id: int,
    datos_cancha: CanchaUpdate,
    admin_id: int = Query(...)
):
    validar_administrador(admin_id)

    canchas = leer_archivo(RUTA_CANCHAS)

    if datos_cancha.nombre.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="El nombre de la cancha es obligatorio"
        )

    if datos_cancha.tipo_superficie.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="El tipo de superficie es obligatorio"
        )

    if datos_cancha.precio_por_hora <= 0:
        raise HTTPException(
            status_code=400,
            detail="El precio por hora debe ser mayor a 0"
        )

    precio_diurno = datos_cancha.precio_diurno
    precio_nocturno = datos_cancha.precio_nocturno

    if precio_diurno is None:
        precio_diurno = datos_cancha.precio_por_hora

    if precio_nocturno is None:
        precio_nocturno = round(datos_cancha.precio_por_hora * 1.2, 2)

    if precio_diurno <= 0 or precio_nocturno <= 0:
        raise HTTPException(
            status_code=400,
            detail="Los precios diurno y nocturno deben ser mayores a 0"
        )

    for cancha in canchas:
        if cancha["id"] == cancha_id:
            cancha["nombre"] = datos_cancha.nombre
            cancha["tipo_superficie"] = datos_cancha.tipo_superficie
            cancha["techada"] = datos_cancha.techada
            cancha["precio_por_hora"] = datos_cancha.precio_por_hora
            cancha["precio_diurno"] = precio_diurno
            cancha["precio_nocturno"] = precio_nocturno
            cancha["activa"] = datos_cancha.activa

            guardar_archivo(RUTA_CANCHAS, canchas)
            return cancha

    raise HTTPException(status_code=404, detail="Cancha no encontrada")


@router.delete("/{cancha_id}")
def dar_baja_cancha(
    cancha_id: int,
    admin_id: int = Query(...)
):
    validar_administrador(admin_id)

    canchas = leer_archivo(RUTA_CANCHAS)

    for cancha in canchas:
        if cancha["id"] == cancha_id:
            cancha["activa"] = False
            guardar_archivo(RUTA_CANCHAS, canchas)

            return {
                "mensaje": "Cancha dada de baja correctamente",
                "cancha": cancha
            }

    raise HTTPException(status_code=404, detail="Cancha no encontrada")


@router.patch("/{cancha_id}/precio")
def modificar_precio_cancha(
    cancha_id: int,
    precio_por_hora: float,
    precio_diurno: float | None = Query(default=None),
    precio_nocturno: float | None = Query(default=None),
    admin_id: int = Query(...)
):
    validar_administrador(admin_id)

    canchas = leer_archivo(RUTA_CANCHAS)

    if precio_por_hora <= 0:
        raise HTTPException(
            status_code=400,
            detail="El precio por hora debe ser mayor a 0"
        )

    if precio_diurno is None:
        precio_diurno = precio_por_hora

    if precio_nocturno is None:
        precio_nocturno = round(precio_por_hora * 1.2, 2)

    if precio_diurno <= 0 or precio_nocturno <= 0:
        raise HTTPException(
            status_code=400,
            detail="Los precios diurno y nocturno deben ser mayores a 0"
        )

    for cancha in canchas:
        if cancha["id"] == cancha_id:
            cancha["precio_por_hora"] = precio_por_hora
            cancha["precio_diurno"] = precio_diurno
            cancha["precio_nocturno"] = precio_nocturno

            guardar_archivo(RUTA_CANCHAS, canchas)

            return {
                "mensaje": "Precios actualizados correctamente",
                "cancha": cancha
            }

    raise HTTPException(status_code=404, detail="Cancha no encontrada")