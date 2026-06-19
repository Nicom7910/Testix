from fastapi import APIRouter, HTTPException, Query
from datetime import date, time, datetime, timedelta

from app.schemas.cancha_schema import (
    CanchaCreate,
    CanchaUpdate,
    CanchaResponse
)
from app.utils.file_manager import (
    leer_archivo,
    guardar_archivo,
    obtener_siguiente_id
)
from app.utils.logger import logger


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
    logger.info(f"Validando permisos de administrador para canchas | admin_id={admin_id}")

    usuarios = leer_archivo(RUTA_USUARIOS)

    for usuario in usuarios:
        if usuario["id"] == admin_id:
            if usuario.get("activo", True) != True:
                logger.warning(
                    f"Accion de cancha rechazada: administrador dado de baja | admin_id={admin_id}"
                )
                raise HTTPException(
                    status_code=403,
                    detail="El usuario administrador está dado de baja"
                )

            if usuario.get("rol") != ROL_ADMINISTRADOR:
                logger.warning(
                    f"Accion de cancha rechazada: usuario sin rol administrador | usuario_id={admin_id} | rol={usuario.get('rol')}"
                )
                raise HTTPException(
                    status_code=403,
                    detail="No tiene permisos de administrador"
                )

            logger.info(f"Administrador validado para canchas | admin_id={admin_id}")
            return usuario

    logger.warning(f"Administrador no encontrado para accion de cancha | admin_id={admin_id}")
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
            logger.info(
                f"Cancha normalizada por campos faltantes | cancha_id={cancha.get('id')}"
            )

    return hubo_cambios


def obtener_intervalo_datetime(fecha_reserva: date, hora_inicio: time, hora_fin: time):
    inicio = datetime.combine(fecha_reserva, hora_inicio)
    fin = datetime.combine(fecha_reserva, hora_fin)

    if hora_fin <= hora_inicio:
        fin = fin + timedelta(days=1)

    return inicio, fin


def validar_fecha_y_horario(fecha_reserva: date, hora_inicio: time, hora_fin: time):
    logger.info(
        f"Validando fecha y horario para disponibilidad | fecha={fecha_reserva} | hora_inicio={hora_inicio} | hora_fin={hora_fin}"
    )

    ahora = datetime.now()
    hoy = ahora.date()

    if fecha_reserva < hoy:
        logger.warning(
            f"Consulta rechazada: fecha anterior a la actual | fecha={fecha_reserva} | hoy={hoy}"
        )
        raise HTTPException(
            status_code=400,
            detail="No se pueden consultar ni reservar fechas anteriores a la actual"
        )

    if hora_inicio < HORA_APERTURA or hora_inicio > HORA_CIERRE:
        logger.warning(
            f"Consulta rechazada: hora de inicio fuera de rango | hora_inicio={hora_inicio}"
        )
        raise HTTPException(
            status_code=400,
            detail="La hora de inicio debe estar entre 08:00 y 23:00"
        )

    if hora_fin != HORA_MEDIANOCHE:
        if hora_fin <= hora_inicio:
            logger.warning(
                f"Consulta rechazada: hora fin menor o igual a inicio | hora_inicio={hora_inicio} | hora_fin={hora_fin}"
            )
            raise HTTPException(
                status_code=400,
                detail="La hora de fin debe ser mayor a la hora de inicio, excepto si finaliza a las 00:00"
            )

        if hora_fin > HORA_CIERRE:
            logger.warning(
                f"Consulta rechazada: hora fin fuera de rango | hora_fin={hora_fin}"
            )
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
        logger.warning(
            f"Consulta rechazada: horario anterior al momento actual | inicio_reserva={inicio_reserva} | ahora={ahora}"
        )
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
    logger.info(
        f"Intento de crear cancha | admin_id={admin_id} | nombre={cancha.nombre} | tipo={cancha.tipo_superficie}"
    )

    validar_administrador(admin_id)

    canchas = leer_archivo(RUTA_CANCHAS)

    if cancha.precio_por_hora <= 0:
        logger.warning(
            f"Alta de cancha rechazada: precio por hora invalido | precio={cancha.precio_por_hora}"
        )
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
        logger.warning(
            f"Alta de cancha rechazada: precios invalidos | diurno={precio_diurno} | nocturno={precio_nocturno}"
        )
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

    logger.info(
        f"Cancha creada correctamente | cancha_id={nueva_cancha['id']} | admin_id={admin_id} | precio={cancha.precio_por_hora}"
    )

    return nueva_cancha


@router.get("/", response_model=list[CanchaResponse])
def listar_canchas():
    logger.info("Solicitud de listado de canchas")

    canchas = leer_archivo(RUTA_CANCHAS)

    if normalizar_canchas(canchas):
        guardar_archivo(RUTA_CANCHAS, canchas)
        logger.info("Listado de canchas normalizado y guardado")

    logger.info(f"Listado de canchas generado | cantidad={len(canchas)}")

    return canchas


@router.get("/disponibles", response_model=list[CanchaResponse])
def listar_canchas_disponibles(
    fecha: date | None = Query(default=None),
    hora_inicio: time | None = Query(default=None),
    hora_fin: time | None = Query(default=None)
):
    logger.info(
        f"Solicitud de canchas disponibles | fecha={fecha} | hora_inicio={hora_inicio} | hora_fin={hora_fin}"
    )

    canchas = leer_archivo(RUTA_CANCHAS)
    reservas = leer_archivo(RUTA_RESERVAS)

    if normalizar_canchas(canchas):
        guardar_archivo(RUTA_CANCHAS, canchas)

    if fecha is None or hora_inicio is None or hora_fin is None:
        disponibles = [
            cancha for cancha in canchas
            if cancha["activa"] == True
        ]

        logger.info(
            f"Canchas activas listadas sin filtro horario | cantidad={len(disponibles)}"
        )

        return disponibles

    validar_fecha_y_horario(fecha, hora_inicio, hora_fin)

    inicio_nuevo, fin_nuevo = obtener_intervalo_datetime(
        fecha,
        hora_inicio,
        hora_fin
    )

    disponibles = []

    for cancha in canchas:
        if cancha["activa"] != True:
            logger.info(
                f"Cancha omitida por estar inactiva | cancha_id={cancha.get('id')}"
            )
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
                    logger.info(
                        f"Cancha no disponible por superposicion | cancha_id={cancha['id']} | reserva_id={reserva.get('id')} | fecha={fecha}"
                    )
                    break

        if cancha_ocupada == False:
            disponibles.append(cancha)

    logger.info(
        f"Consulta de disponibilidad finalizada | fecha={fecha} | cantidad_disponible={len(disponibles)}"
    )

    return disponibles


@router.get("/{cancha_id}", response_model=CanchaResponse)
def obtener_cancha(cancha_id: int):
    logger.info(f"Solicitud de detalle de cancha | cancha_id={cancha_id}")

    canchas = leer_archivo(RUTA_CANCHAS)

    if normalizar_canchas(canchas):
        guardar_archivo(RUTA_CANCHAS, canchas)

    for cancha in canchas:
        if cancha["id"] == cancha_id:
            logger.info(f"Cancha encontrada | cancha_id={cancha_id}")
            return cancha

    logger.warning(f"Cancha no encontrada | cancha_id={cancha_id}")
    raise HTTPException(status_code=404, detail="Cancha no encontrada")


@router.put("/{cancha_id}", response_model=CanchaResponse)
def modificar_cancha(
    cancha_id: int,
    datos_cancha: CanchaUpdate,
    admin_id: int = Query(...)
):
    logger.info(
        f"Intento de modificar cancha | cancha_id={cancha_id} | admin_id={admin_id}"
    )

    validar_administrador(admin_id)

    canchas = leer_archivo(RUTA_CANCHAS)

    if datos_cancha.nombre.strip() == "":
        logger.warning(
            f"Modificacion de cancha rechazada: nombre vacio | cancha_id={cancha_id}"
        )
        raise HTTPException(
            status_code=400,
            detail="El nombre de la cancha es obligatorio"
        )

    if datos_cancha.tipo_superficie.strip() == "":
        logger.warning(
            f"Modificacion de cancha rechazada: tipo de superficie vacio | cancha_id={cancha_id}"
        )
        raise HTTPException(
            status_code=400,
            detail="El tipo de superficie es obligatorio"
        )

    if datos_cancha.precio_por_hora <= 0:
        logger.warning(
            f"Modificacion de cancha rechazada: precio por hora invalido | cancha_id={cancha_id} | precio={datos_cancha.precio_por_hora}"
        )
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
        logger.warning(
            f"Modificacion de cancha rechazada: precios invalidos | cancha_id={cancha_id} | diurno={precio_diurno} | nocturno={precio_nocturno}"
        )
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

            logger.info(
                f"Cancha modificada correctamente | cancha_id={cancha_id} | admin_id={admin_id} | activa={datos_cancha.activa}"
            )

            return cancha

    logger.warning(
        f"Modificacion de cancha rechazada: cancha no encontrada | cancha_id={cancha_id}"
    )
    raise HTTPException(status_code=404, detail="Cancha no encontrada")


@router.delete("/{cancha_id}")
def dar_baja_cancha(
    cancha_id: int,
    admin_id: int = Query(...)
):
    logger.info(
        f"Intento de baja de cancha | cancha_id={cancha_id} | admin_id={admin_id}"
    )

    validar_administrador(admin_id)

    canchas = leer_archivo(RUTA_CANCHAS)

    for cancha in canchas:
        if cancha["id"] == cancha_id:
            cancha["activa"] = False

            guardar_archivo(RUTA_CANCHAS, canchas)

            logger.info(
                f"Cancha dada de baja correctamente | cancha_id={cancha_id} | admin_id={admin_id}"
            )

            return {
                "mensaje": "Cancha dada de baja correctamente",
                "cancha": cancha
            }

    logger.warning(
        f"Baja de cancha rechazada: cancha no encontrada | cancha_id={cancha_id}"
    )
    raise HTTPException(status_code=404, detail="Cancha no encontrada")


@router.patch("/{cancha_id}/precio")
def modificar_precio_cancha(
    cancha_id: int,
    precio_por_hora: float,
    precio_diurno: float | None = Query(default=None),
    precio_nocturno: float | None = Query(default=None),
    admin_id: int = Query(...)
):
    logger.info(
        f"Intento de modificar precio de cancha | cancha_id={cancha_id} | admin_id={admin_id} | precio_por_hora={precio_por_hora}"
    )

    validar_administrador(admin_id)

    canchas = leer_archivo(RUTA_CANCHAS)

    if precio_por_hora <= 0:
        logger.warning(
            f"Modificacion de precio rechazada: precio por hora invalido | cancha_id={cancha_id} | precio={precio_por_hora}"
        )
        raise HTTPException(
            status_code=400,
            detail="El precio por hora debe ser mayor a 0"
        )

    if precio_diurno is None:
        precio_diurno = precio_por_hora

    if precio_nocturno is None:
        precio_nocturno = round(precio_por_hora * 1.2, 2)

    if precio_diurno <= 0 or precio_nocturno <= 0:
        logger.warning(
            f"Modificacion de precio rechazada: precios invalidos | cancha_id={cancha_id} | diurno={precio_diurno} | nocturno={precio_nocturno}"
        )
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

            logger.info(
                f"Precio de cancha actualizado correctamente | cancha_id={cancha_id} | admin_id={admin_id} | precio_por_hora={precio_por_hora} | precio_diurno={precio_diurno} | precio_nocturno={precio_nocturno}"
            )

            return {
                "mensaje": "Precios actualizados correctamente",
                "cancha": cancha
            }

    logger.warning(
        f"Modificacion de precio rechazada: cancha no encontrada | cancha_id={cancha_id}"
    )
    raise HTTPException(status_code=404, detail="Cancha no encontrada")