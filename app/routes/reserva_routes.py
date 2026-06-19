from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta, date, time
import re

from app.schemas.reserva_schema import (
    ReservaCreate,
    ReservaUpdateAdmin,
    ReservaResponse,
    CancelarReservaRequest,
    PagoReservaRequest
)
from app.utils.file_manager import (
    leer_archivo,
    guardar_archivo,
    obtener_siguiente_id
)
from app.utils.logger import logger


router = APIRouter(
    prefix="/reservas",
    tags=["Reservas"]
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

ESTADO_DEVOLUCION_NO_APLICA = "no_aplica"
ESTADO_DEVOLUCION_PENDIENTE = "pendiente"
ESTADO_DEVOLUCION_REALIZADA = "realizada"

ESTADOS_RESERVA_VALIDOS = [
    ESTADO_RESERVA_PENDIENTE,
    ESTADO_RESERVA_CONFIRMADA,
    ESTADO_RESERVA_CANCELADA,
    ESTADO_RESERVA_FINALIZADA
]

ESTADOS_PAGO_VALIDOS = [
    ESTADO_PAGO_PENDIENTE,
    ESTADO_PAGO_PAGADO,
    ESTADO_PAGO_RECHAZADO
]

HORA_APERTURA = time(8, 0)
HORA_CIERRE = time(23, 0)
HORA_MEDIANOCHE = time(0, 0)
HORA_INICIO_NOCTURNO = time(18, 0)
MINUTOS_MINIMOS_REEMBOLSO = 30


def obtener_usuario_por_id(usuario_id: int):
    logger.info(f"Buscando usuario | usuario_id={usuario_id}")

    usuarios = leer_archivo(RUTA_USUARIOS)

    for usuario in usuarios:
        if usuario["id"] == usuario_id:
            if usuario.get("activo", True) != True:
                logger.warning(
                    f"Usuario dado de baja intentó operar | usuario_id={usuario_id}"
                )
                raise HTTPException(
                    status_code=403,
                    detail="El usuario está dado de baja"
                )

            logger.info(f"Usuario encontrado correctamente | usuario_id={usuario_id}")
            return usuario

    logger.warning(f"Usuario no encontrado | usuario_id={usuario_id}")
    raise HTTPException(
        status_code=404,
        detail="Usuario no encontrado"
    )


def validar_administrador(admin_id: int):
    logger.info(f"Validando administrador para reservas | admin_id={admin_id}")

    usuario = obtener_usuario_por_id(admin_id)

    if usuario.get("rol") != ROL_ADMINISTRADOR:
        logger.warning(
            f"Acceso rechazado a reservas por rol insuficiente | usuario_id={admin_id} | rol={usuario.get('rol')}"
        )
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos de administrador"
        )

    logger.info(f"Administrador validado correctamente | admin_id={admin_id}")
    return usuario


def convertir_hora(texto_hora: str):
    try:
        return datetime.strptime(texto_hora, "%H:%M:%S").time()
    except ValueError:
        return datetime.strptime(texto_hora, "%H:%M").time()


def obtener_intervalo_datetime(fecha_reserva: date, hora_inicio: time, hora_fin: time):
    inicio = datetime.combine(fecha_reserva, hora_inicio)
    fin = datetime.combine(fecha_reserva, hora_fin)

    if hora_fin <= hora_inicio:
        fin = fin + timedelta(days=1)

    return inicio, fin


def obtener_fecha_hora_inicio(reserva: dict):
    fecha_reserva = datetime.strptime(reserva["fecha"], "%Y-%m-%d").date()
    hora_inicio = convertir_hora(reserva["hora_inicio"])
    return datetime.combine(fecha_reserva, hora_inicio)


def obtener_fecha_hora_fin(reserva: dict):
    fecha_reserva = datetime.strptime(reserva["fecha"], "%Y-%m-%d").date()
    hora_inicio = convertir_hora(reserva["hora_inicio"])
    hora_fin = convertir_hora(reserva["hora_fin"])

    _, fin = obtener_intervalo_datetime(fecha_reserva, hora_inicio, hora_fin)
    return fin


def obtener_limite_pago(reserva: dict):
    fecha_creacion = reserva.get("fecha_creacion")

    if fecha_creacion is not None:
        try:
            return datetime.strptime(
                fecha_creacion,
                "%Y-%m-%d %H:%M:%S"
            ) + timedelta(hours=24)
        except Exception as error:
            logger.error(
                f"No se pudo calcular limite de pago desde fecha_creacion | reserva_id={reserva.get('id')} | error={str(error)}"
            )

    return datetime.now() + timedelta(hours=24)


def hay_superposicion(inicio_nuevo, fin_nuevo, inicio_existente, fin_existente):
    return inicio_nuevo < fin_existente and fin_nuevo > inicio_existente


def normalizar_cancha(cancha: dict):
    if "precio_diurno" not in cancha or cancha["precio_diurno"] is None:
        cancha["precio_diurno"] = cancha["precio_por_hora"]

    if "precio_nocturno" not in cancha or cancha["precio_nocturno"] is None:
        cancha["precio_nocturno"] = round(cancha["precio_por_hora"] * 1.2, 2)

    return cancha


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

    if "fecha_creacion" not in reserva:
        reserva["fecha_creacion"] = None

    if "motivo_cancelacion" not in reserva:
        reserva["motivo_cancelacion"] = None

    if "requiere_devolucion" not in reserva:
        reserva["requiere_devolucion"] = False

    if "monto_devolucion" not in reserva:
        reserva["monto_devolucion"] = 0

    if "estado_devolucion" not in reserva:
        reserva["estado_devolucion"] = ESTADO_DEVOLUCION_NO_APLICA

    reserva["activa"] = reserva["estado_reserva"] == ESTADO_RESERVA_CONFIRMADA
    reserva["pagada"] = reserva["estado_pago"] == ESTADO_PAGO_PAGADO

    return reserva


def validar_fecha_y_horario(fecha_reserva: date, hora_inicio: time, hora_fin: time):
    logger.info(
        f"Validando fecha y horario de reserva | fecha={fecha_reserva} | hora_inicio={hora_inicio} | hora_fin={hora_fin}"
    )

    ahora = datetime.now()
    hoy = ahora.date()

    if fecha_reserva < hoy:
        logger.warning(
            f"Reserva rechazada: fecha anterior a la actual | fecha={fecha_reserva} | hoy={hoy}"
        )
        raise HTTPException(
            status_code=400,
            detail="No se pueden crear reservas con fecha anterior a la actual"
        )

    if hora_inicio < HORA_APERTURA or hora_inicio > HORA_CIERRE:
        logger.warning(
            f"Reserva rechazada: hora de inicio fuera de rango | hora_inicio={hora_inicio}"
        )
        raise HTTPException(
            status_code=400,
            detail="La hora de inicio debe estar entre 08:00 y 23:00"
        )

    if hora_fin != HORA_MEDIANOCHE:
        if hora_fin <= hora_inicio:
            logger.warning(
                f"Reserva rechazada: hora fin menor o igual a inicio | hora_inicio={hora_inicio} | hora_fin={hora_fin}"
            )
            raise HTTPException(
                status_code=400,
                detail="La hora de fin debe ser mayor a la hora de inicio, excepto si finaliza a las 00:00"
            )

        if hora_fin > HORA_CIERRE:
            logger.warning(
                f"Reserva rechazada: hora fin fuera de rango | hora_fin={hora_fin}"
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
            f"Reserva rechazada: horario anterior al momento actual | inicio_reserva={inicio_reserva} | ahora={ahora}"
        )
        raise HTTPException(
            status_code=400,
            detail="No se pueden crear reservas en un horario anterior al momento actual"
        )


def validar_pago(datos_pago: PagoReservaRequest):
    logger.info("Validando datos de pago de seña")

    numero = datos_pago.numero_tarjeta.replace(" ", "").replace("-", "")

    if not numero.isdigit() or len(numero) != 16:
        logger.warning("Pago rechazado: numero de tarjeta invalido")
        raise HTTPException(
            status_code=400,
            detail="El número de tarjeta debe tener 16 dígitos numéricos"
        )

    if datos_pago.nombre_titular.strip() == "":
        logger.warning("Pago rechazado: nombre del titular vacio")
        raise HTTPException(
            status_code=400,
            detail="Debe ingresar el nombre del titular"
        )

    if not re.match(r"^(0[1-9]|1[0-2])\/\d{2}$", datos_pago.vencimiento.strip()):
        logger.warning(
            f"Pago rechazado: vencimiento con formato invalido | vencimiento={datos_pago.vencimiento}"
        )
        raise HTTPException(
            status_code=400,
            detail="El vencimiento debe tener formato MM/AA"
        )

    mes, anio = datos_pago.vencimiento.strip().split("/")
    mes = int(mes)
    anio = int("20" + anio)

    ahora = datetime.now()
    anio_actual = ahora.year
    mes_actual = ahora.month

    if anio < anio_actual or (anio == anio_actual and mes < mes_actual):
        logger.warning(
            f"Pago rechazado: tarjeta vencida | mes={mes} | anio={anio} | mes_actual={mes_actual} | anio_actual={anio_actual}"
        )
        raise HTTPException(
            status_code=400,
            detail="La tarjeta se encuentra vencida"
        )

    codigo = datos_pago.codigo_seguridad.strip()

    if not codigo.isdigit() or len(codigo) not in [3, 4]:
        logger.warning("Pago rechazado: codigo de seguridad invalido")
        raise HTTPException(
            status_code=400,
            detail="El código de seguridad debe tener 3 o 4 dígitos"
        )

    logger.info("Datos de pago validados correctamente")


def ordenar_reservas_recientes(reservas: list):
    def clave(reserva):
        try:
            fecha_reserva = datetime.strptime(reserva["fecha"], "%Y-%m-%d").date()
            hora_inicio = convertir_hora(reserva["hora_inicio"])
            return datetime.combine(fecha_reserva, hora_inicio)
        except Exception:
            return datetime.min

    return sorted(reservas, key=clave, reverse=True)


def actualizar_reservas_por_tiempo(reservas: list):
    ahora = datetime.now()
    hubo_cambios = False

    for reserva in reservas:
        reserva_original = reserva.copy()
        normalizar_reserva(reserva)

        if reserva["estado_reserva"] == ESTADO_RESERVA_CONFIRMADA:
            fecha_hora_fin = obtener_fecha_hora_fin(reserva)

            if fecha_hora_fin < ahora:
                reserva["estado_reserva"] = ESTADO_RESERVA_FINALIZADA
                reserva["activa"] = False

                logger.info(
                    f"Reserva finalizada automaticamente por tiempo cumplido | reserva_id={reserva.get('id')} | fecha_hora_fin={fecha_hora_fin}"
                )

        if (
            reserva["estado_reserva"] == ESTADO_RESERVA_PENDIENTE
            and reserva["estado_pago"] != ESTADO_PAGO_PAGADO
        ):
            limite_pago = obtener_limite_pago(reserva)

            if ahora > limite_pago:
                reserva["estado_reserva"] = ESTADO_RESERVA_CANCELADA
                reserva["activa"] = False
                reserva["motivo_cancelacion"] = (
                    "Cancelada automáticamente por no pagar la seña "
                    "dentro de las 24 horas posteriores a la creación de la reserva"
                )

                logger.warning(
                    f"Reserva cancelada automaticamente por vencimiento de pago | reserva_id={reserva.get('id')} | limite_pago={limite_pago} | ahora={ahora}"
                )

        if reserva != reserva_original:
            hubo_cambios = True

    return hubo_cambios


def obtener_reservas_actualizadas():
    reservas = leer_archivo(RUTA_RESERVAS)

    if actualizar_reservas_por_tiempo(reservas):
        guardar_archivo(RUTA_RESERVAS, reservas)
        logger.info("Reservas actualizadas automaticamente por reglas de tiempo")

    return reservas


def obtener_cancha_activa_por_id(cancha_id: int):
    logger.info(f"Buscando cancha activa | cancha_id={cancha_id}")

    canchas = leer_archivo(RUTA_CANCHAS)

    for cancha in canchas:
        if cancha["id"] == cancha_id:
            normalizar_cancha(cancha)

            if cancha["activa"] != True:
                logger.warning(
                    f"Cancha deshabilitada utilizada para reserva | cancha_id={cancha_id}"
                )
                raise HTTPException(
                    status_code=400,
                    detail="La cancha seleccionada está deshabilitada"
                )

            logger.info(f"Cancha activa encontrada | cancha_id={cancha_id}")
            return cancha

    logger.warning(f"Cancha inexistente | cancha_id={cancha_id}")
    raise HTTPException(
        status_code=404,
        detail="La cancha no existe"
    )


def calcular_importes(cancha: dict, fecha_reserva, hora_inicio, hora_fin):
    validar_fecha_y_horario(fecha_reserva, hora_inicio, hora_fin)

    inicio_datetime, fin_datetime = obtener_intervalo_datetime(
        fecha_reserva,
        hora_inicio,
        hora_fin
    )

    cantidad_horas = 0
    monto_total = 0
    cursor = inicio_datetime

    while cursor < fin_datetime:
        siguiente_tramo = cursor + timedelta(minutes=30)

        if siguiente_tramo > fin_datetime:
            siguiente_tramo = fin_datetime

        horas_tramo = (siguiente_tramo - cursor).total_seconds() / 3600

        if cursor.time() >= HORA_INICIO_NOCTURNO:
            precio = cancha["precio_nocturno"]
        else:
            precio = cancha["precio_diurno"]

        monto_total += precio * horas_tramo
        cantidad_horas += horas_tramo
        cursor = siguiente_tramo

    sena = monto_total * 0.5

    logger.info(
        f"Importes calculados | cancha_id={cancha.get('id')} | horas={cantidad_horas} | monto_total={round(monto_total, 2)} | sena={round(sena, 2)}"
    )

    return cantidad_horas, round(monto_total, 2), round(sena, 2)


def validar_superposicion_reserva(
    reservas: list,
    reserva_id_actual: int | None,
    cancha_id: int,
    fecha_reserva: str,
    hora_inicio,
    hora_fin
):
    logger.info(
        f"Validando superposicion | cancha_id={cancha_id} | fecha={fecha_reserva} | hora_inicio={hora_inicio} | hora_fin={hora_fin}"
    )

    fecha_obj = datetime.strptime(fecha_reserva, "%Y-%m-%d").date()

    inicio_nuevo, fin_nuevo = obtener_intervalo_datetime(
        fecha_obj,
        hora_inicio,
        hora_fin
    )

    for reserva in reservas:
        normalizar_reserva(reserva)

        if reserva_id_actual is not None and reserva["id"] == reserva_id_actual:
            continue

        if (
            reserva["cancha_id"] == cancha_id
            and reserva["fecha"] == fecha_reserva
            and reserva["estado_reserva"] in [
                ESTADO_RESERVA_PENDIENTE,
                ESTADO_RESERVA_CONFIRMADA
            ]
        ):
            reserva_inicio = convertir_hora(reserva["hora_inicio"])
            reserva_fin = convertir_hora(reserva["hora_fin"])

            inicio_existente, fin_existente = obtener_intervalo_datetime(
                fecha_obj,
                reserva_inicio,
                reserva_fin
            )

            if hay_superposicion(
                inicio_nuevo,
                fin_nuevo,
                inicio_existente,
                fin_existente
            ):
                logger.warning(
                    f"Reserva rechazada por superposicion | reserva_existente_id={reserva.get('id')} | cancha_id={cancha_id} | fecha={fecha_reserva}"
                )
                raise HTTPException(
                    status_code=400,
                    detail="La cancha ya tiene una reserva en ese rango horario"
                )

    logger.info(
        f"No se detecto superposicion | cancha_id={cancha_id} | fecha={fecha_reserva}"
    )


def aplicar_datos_de_devolucion(reserva: dict):
    if reserva["estado_pago"] == ESTADO_PAGO_PAGADO:
        reserva["requiere_devolucion"] = True
        reserva["monto_devolucion"] = reserva.get("sena", 0)
        reserva["estado_devolucion"] = ESTADO_DEVOLUCION_PENDIENTE
    else:
        reserva["requiere_devolucion"] = False
        reserva["monto_devolucion"] = 0
        reserva["estado_devolucion"] = ESTADO_DEVOLUCION_NO_APLICA


def aplicar_cancelacion_con_regla_reembolso(reserva: dict):
    ahora = datetime.now()

    reserva["estado_reserva"] = ESTADO_RESERVA_CANCELADA
    reserva["activa"] = False

    if reserva["estado_pago"] != ESTADO_PAGO_PAGADO:
        reserva["requiere_devolucion"] = False
        reserva["monto_devolucion"] = 0
        reserva["estado_devolucion"] = ESTADO_DEVOLUCION_NO_APLICA

        logger.info(
            f"Reserva cancelada sin devolucion por falta de pago | reserva_id={reserva.get('id')}"
        )

        return (
            "Reserva cancelada correctamente.\n"
            "No corresponde devolución porque la seña no estaba pagada.",
            "sin_pago"
        )

    fecha_hora_inicio = obtener_fecha_hora_inicio(reserva)
    limite_reembolso = fecha_hora_inicio - timedelta(minutes=MINUTOS_MINIMOS_REEMBOLSO)

    if ahora > limite_reembolso:
        reserva["requiere_devolucion"] = False
        reserva["monto_devolucion"] = 0
        reserva["estado_devolucion"] = ESTADO_DEVOLUCION_NO_APLICA

        logger.warning(
            f"Reserva cancelada sin reembolso por poca anticipacion | reserva_id={reserva.get('id')} | ahora={ahora} | limite_reembolso={limite_reembolso}"
        )

        return (
            "Reserva cancelada correctamente.\n"
            "No se realizará reembolso de la seña porque la cancelación fue realizada con menos de 30 minutos de anticipación.",
            "sin_reembolso"
        )

    reserva["requiere_devolucion"] = True
    reserva["monto_devolucion"] = reserva.get("sena", 0)
    reserva["estado_devolucion"] = ESTADO_DEVOLUCION_PENDIENTE

    logger.info(
        f"Reserva cancelada con devolucion pendiente | reserva_id={reserva.get('id')} | monto_devolucion={reserva.get('monto_devolucion')}"
    )

    return (
        "Reserva cancelada correctamente.\n"
        "Se generó una devolución pendiente por el monto de la seña.",
        "con_reembolso"
    )


@router.post("/", response_model=ReservaResponse)
def crear_reserva(reserva: ReservaCreate):
    logger.info(
        f"Intento de crear reserva | usuario_id={reserva.usuario_id} | cancha_id={reserva.cancha_id} | fecha={reserva.fecha} | hora_inicio={reserva.hora_inicio} | hora_fin={reserva.hora_fin}"
    )

    reservas = obtener_reservas_actualizadas()
    usuarios = leer_archivo(RUTA_USUARIOS)

    usuario_encontrado = None

    for usuario in usuarios:
        if usuario["id"] == reserva.usuario_id and usuario.get("activo", True) == True:
            usuario_encontrado = usuario

    if usuario_encontrado is None:
        logger.warning(
            f"Reserva rechazada: usuario inexistente o dado de baja | usuario_id={reserva.usuario_id}"
        )
        raise HTTPException(
            status_code=404,
            detail="El usuario no existe o está dado de baja"
        )

    cancha_encontrada = obtener_cancha_activa_por_id(reserva.cancha_id)

    hora_inicio = reserva.hora_inicio
    hora_fin = reserva.hora_fin

    cantidad_horas, monto_total, sena = calcular_importes(
        cancha_encontrada,
        reserva.fecha,
        hora_inicio,
        hora_fin
    )

    validar_superposicion_reserva(
        reservas=reservas,
        reserva_id_actual=None,
        cancha_id=reserva.cancha_id,
        fecha_reserva=str(reserva.fecha),
        hora_inicio=hora_inicio,
        hora_fin=hora_fin
    )

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
        "estado_reserva": ESTADO_RESERVA_PENDIENTE,
        "estado_pago": ESTADO_PAGO_PENDIENTE,
        "activa": False,
        "pagada": False,
        "motivo_cancelacion": None,
        "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "requiere_devolucion": False,
        "monto_devolucion": 0,
        "estado_devolucion": ESTADO_DEVOLUCION_NO_APLICA
    }

    reservas.append(nueva_reserva)
    guardar_archivo(RUTA_RESERVAS, reservas)

    logger.info(
        f"Reserva creada correctamente | reserva_id={nueva_reserva['id']} | usuario_id={reserva.usuario_id} | cancha_id={reserva.cancha_id} | monto_total={monto_total} | sena={sena}"
    )

    return nueva_reserva


@router.get("/", response_model=list[ReservaResponse])
def listar_reservas(admin_id: int = Query(...)):
    logger.info(f"Solicitud de listado total de reservas | admin_id={admin_id}")

    validar_administrador(admin_id)
    reservas = obtener_reservas_actualizadas()

    logger.info(
        f"Listado total de reservas generado | admin_id={admin_id} | cantidad={len(reservas)}"
    )

    return ordenar_reservas_recientes(reservas)


@router.get("/activas", response_model=list[ReservaResponse])
def listar_reservas_activas(admin_id: int = Query(...)):
    logger.info(f"Solicitud de reservas activas | admin_id={admin_id}")

    validar_administrador(admin_id)
    reservas = obtener_reservas_actualizadas()

    reservas_filtradas = [
        reserva for reserva in reservas
        if reserva["estado_reserva"] == ESTADO_RESERVA_CONFIRMADA
    ]

    logger.info(
        f"Reservas activas listadas | admin_id={admin_id} | cantidad={len(reservas_filtradas)}"
    )

    return ordenar_reservas_recientes(reservas_filtradas)


@router.get("/pendientes", response_model=list[ReservaResponse])
def listar_reservas_pendientes(admin_id: int = Query(...)):
    logger.info(f"Solicitud de reservas pendientes | admin_id={admin_id}")

    validar_administrador(admin_id)
    reservas = obtener_reservas_actualizadas()

    reservas_filtradas = [
        reserva for reserva in reservas
        if reserva["estado_reserva"] == ESTADO_RESERVA_PENDIENTE
    ]

    logger.info(
        f"Reservas pendientes listadas | admin_id={admin_id} | cantidad={len(reservas_filtradas)}"
    )

    return ordenar_reservas_recientes(reservas_filtradas)


@router.get("/canceladas", response_model=list[ReservaResponse])
def listar_reservas_canceladas(admin_id: int = Query(...)):
    logger.info(f"Solicitud de reservas canceladas | admin_id={admin_id}")

    validar_administrador(admin_id)
    reservas = obtener_reservas_actualizadas()

    reservas_filtradas = [
        reserva for reserva in reservas
        if reserva["estado_reserva"] == ESTADO_RESERVA_CANCELADA
    ]

    logger.info(
        f"Reservas canceladas listadas | admin_id={admin_id} | cantidad={len(reservas_filtradas)}"
    )

    return ordenar_reservas_recientes(reservas_filtradas)


@router.get("/pasadas", response_model=list[ReservaResponse])
def listar_reservas_pasadas(admin_id: int = Query(...)):
    logger.info(f"Solicitud de reservas pasadas | admin_id={admin_id}")

    validar_administrador(admin_id)
    reservas = obtener_reservas_actualizadas()

    reservas_filtradas = [
        reserva for reserva in reservas
        if reserva["estado_reserva"] == ESTADO_RESERVA_FINALIZADA
    ]

    logger.info(
        f"Reservas pasadas listadas | admin_id={admin_id} | cantidad={len(reservas_filtradas)}"
    )

    return ordenar_reservas_recientes(reservas_filtradas)


@router.get("/usuario/{usuario_id}/activas", response_model=list[ReservaResponse])
def listar_reservas_activas_usuario(usuario_id: int):
    logger.info(f"Solicitud de reservas activas de usuario | usuario_id={usuario_id}")

    reservas = obtener_reservas_actualizadas()

    reservas_filtradas = [
        reserva for reserva in reservas
        if reserva["usuario_id"] == usuario_id
        and reserva["estado_reserva"] == ESTADO_RESERVA_CONFIRMADA
    ]

    logger.info(
        f"Reservas activas de usuario listadas | usuario_id={usuario_id} | cantidad={len(reservas_filtradas)}"
    )

    return ordenar_reservas_recientes(reservas_filtradas)


@router.get("/usuario/{usuario_id}/pendientes", response_model=list[ReservaResponse])
def listar_reservas_pendientes_usuario(usuario_id: int):
    logger.info(f"Solicitud de reservas pendientes de usuario | usuario_id={usuario_id}")

    reservas = obtener_reservas_actualizadas()

    reservas_filtradas = [
        reserva for reserva in reservas
        if reserva["usuario_id"] == usuario_id
        and reserva["estado_reserva"] == ESTADO_RESERVA_PENDIENTE
    ]

    logger.info(
        f"Reservas pendientes de usuario listadas | usuario_id={usuario_id} | cantidad={len(reservas_filtradas)}"
    )

    return ordenar_reservas_recientes(reservas_filtradas)


@router.get("/usuario/{usuario_id}/canceladas", response_model=list[ReservaResponse])
def listar_reservas_canceladas_usuario(usuario_id: int):
    logger.info(f"Solicitud de reservas canceladas de usuario | usuario_id={usuario_id}")

    reservas = obtener_reservas_actualizadas()

    reservas_filtradas = [
        reserva for reserva in reservas
        if reserva["usuario_id"] == usuario_id
        and reserva["estado_reserva"] == ESTADO_RESERVA_CANCELADA
    ]

    logger.info(
        f"Reservas canceladas de usuario listadas | usuario_id={usuario_id} | cantidad={len(reservas_filtradas)}"
    )

    return ordenar_reservas_recientes(reservas_filtradas)


@router.get("/usuario/{usuario_id}/pasadas", response_model=list[ReservaResponse])
def listar_reservas_pasadas_usuario(usuario_id: int):
    logger.info(f"Solicitud de reservas pasadas de usuario | usuario_id={usuario_id}")

    reservas = obtener_reservas_actualizadas()

    reservas_filtradas = [
        reserva for reserva in reservas
        if reserva["usuario_id"] == usuario_id
        and reserva["estado_reserva"] == ESTADO_RESERVA_FINALIZADA
    ]

    logger.info(
        f"Reservas pasadas de usuario listadas | usuario_id={usuario_id} | cantidad={len(reservas_filtradas)}"
    )

    return ordenar_reservas_recientes(reservas_filtradas)


@router.get("/usuario/{usuario_id}/historial", response_model=list[ReservaResponse])
def listar_historial_usuario(usuario_id: int):
    logger.info(f"Solicitud de historial de reservas | usuario_id={usuario_id}")

    reservas = obtener_reservas_actualizadas()

    reservas_filtradas = [
        reserva for reserva in reservas
        if reserva["usuario_id"] == usuario_id
    ]

    logger.info(
        f"Historial de reservas generado | usuario_id={usuario_id} | cantidad={len(reservas_filtradas)}"
    )

    return ordenar_reservas_recientes(reservas_filtradas)


@router.put("/{reserva_id}", response_model=ReservaResponse)
def modificar_reserva_admin(
    reserva_id: int,
    datos_reserva: ReservaUpdateAdmin,
    admin_id: int = Query(...)
):
    logger.info(
        f"Intento de modificacion administrativa de reserva | reserva_id={reserva_id} | admin_id={admin_id}"
    )

    validar_administrador(admin_id)

    reservas = obtener_reservas_actualizadas()

    if datos_reserva.estado_reserva not in ESTADOS_RESERVA_VALIDOS:
        logger.warning(
            f"Modificacion rechazada: estado de reserva invalido | reserva_id={reserva_id} | estado={datos_reserva.estado_reserva}"
        )
        raise HTTPException(
            status_code=400,
            detail="Estado de reserva inválido"
        )

    if datos_reserva.estado_pago not in ESTADOS_PAGO_VALIDOS:
        logger.warning(
            f"Modificacion rechazada: estado de pago invalido | reserva_id={reserva_id} | estado_pago={datos_reserva.estado_pago}"
        )
        raise HTTPException(
            status_code=400,
            detail="Estado de pago inválido"
        )

    cancha_encontrada = obtener_cancha_activa_por_id(datos_reserva.cancha_id)

    hora_inicio = datos_reserva.hora_inicio
    hora_fin = datos_reserva.hora_fin

    cantidad_horas, monto_total, sena = calcular_importes(
        cancha_encontrada,
        datos_reserva.fecha,
        hora_inicio,
        hora_fin
    )

    if datos_reserva.estado_reserva in [
        ESTADO_RESERVA_PENDIENTE,
        ESTADO_RESERVA_CONFIRMADA
    ]:
        validar_superposicion_reserva(
            reservas=reservas,
            reserva_id_actual=reserva_id,
            cancha_id=datos_reserva.cancha_id,
            fecha_reserva=str(datos_reserva.fecha),
            hora_inicio=hora_inicio,
            hora_fin=hora_fin
        )

    for reserva in reservas:
        normalizar_reserva(reserva)

        if reserva["id"] == reserva_id:
            reserva["cancha_id"] = datos_reserva.cancha_id
            reserva["fecha"] = str(datos_reserva.fecha)
            reserva["hora_inicio"] = hora_inicio.strftime("%H:%M:%S")
            reserva["hora_fin"] = hora_fin.strftime("%H:%M:%S")
            reserva["cantidad_horas"] = cantidad_horas
            reserva["monto_total"] = monto_total
            reserva["sena"] = sena
            reserva["estado_reserva"] = datos_reserva.estado_reserva
            reserva["estado_pago"] = datos_reserva.estado_pago
            reserva["activa"] = datos_reserva.estado_reserva == ESTADO_RESERVA_CONFIRMADA
            reserva["pagada"] = datos_reserva.estado_pago == ESTADO_PAGO_PAGADO

            if datos_reserva.estado_reserva == ESTADO_RESERVA_CANCELADA:
                mensaje, tipo_reembolso = aplicar_cancelacion_con_regla_reembolso(reserva)
                logger.info(
                    f"Reserva cancelada desde modificacion administrativa | reserva_id={reserva_id} | admin_id={admin_id} | tipo_reembolso={tipo_reembolso}"
                )
            else:
                reserva["motivo_cancelacion"] = None
                reserva["requiere_devolucion"] = False
                reserva["monto_devolucion"] = 0
                reserva["estado_devolucion"] = ESTADO_DEVOLUCION_NO_APLICA

            guardar_archivo(RUTA_RESERVAS, reservas)

            logger.info(
                f"Reserva modificada correctamente por administrador | reserva_id={reserva_id} | admin_id={admin_id}"
            )

            return reserva

    logger.warning(
        f"Modificacion rechazada: reserva no encontrada | reserva_id={reserva_id} | admin_id={admin_id}"
    )
    raise HTTPException(status_code=404, detail="Reserva no encontrada")


@router.put("/{reserva_id}/pagar", response_model=ReservaResponse)
def pagar_sena_reserva(
    reserva_id: int,
    datos_pago: PagoReservaRequest
):
    logger.info(f"Intento de pago de seña | reserva_id={reserva_id}")

    reservas = obtener_reservas_actualizadas()
    ahora = datetime.now()

    validar_pago(datos_pago)

    for reserva in reservas:
        normalizar_reserva(reserva)

        if reserva["id"] == reserva_id:
            if reserva["estado_reserva"] == ESTADO_RESERVA_CANCELADA:
                logger.warning(
                    f"Pago rechazado: reserva cancelada | reserva_id={reserva_id}"
                )
                raise HTTPException(
                    status_code=400,
                    detail="No se puede pagar una reserva cancelada"
                )

            if reserva["estado_reserva"] == ESTADO_RESERVA_FINALIZADA:
                logger.warning(
                    f"Pago rechazado: reserva finalizada | reserva_id={reserva_id}"
                )
                raise HTTPException(
                    status_code=400,
                    detail="No se puede pagar una reserva finalizada"
                )

            if reserva["estado_pago"] == ESTADO_PAGO_PAGADO:
                logger.warning(
                    f"Pago rechazado: reserva ya pagada | reserva_id={reserva_id}"
                )
                raise HTTPException(
                    status_code=400,
                    detail="La reserva ya fue pagada"
                )

            limite_pago = obtener_limite_pago(reserva)

            if ahora > limite_pago:
                reserva["estado_reserva"] = ESTADO_RESERVA_CANCELADA
                reserva["activa"] = False
                reserva["motivo_cancelacion"] = (
                    "Cancelada automáticamente por no pagar la seña "
                    "dentro de las 24 horas posteriores a la creación de la reserva"
                )

                guardar_archivo(RUTA_RESERVAS, reservas)

                logger.warning(
                    f"Pago rechazado: plazo vencido y reserva cancelada automaticamente | reserva_id={reserva_id} | limite_pago={limite_pago} | ahora={ahora}"
                )

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "El plazo para pagar la seña venció.\n"
                        "Debía pagarse dentro de las 24 horas posteriores a la creación de la reserva."
                    )
                )

            numero = datos_pago.numero_tarjeta.replace(" ", "").replace("-", "")

            if numero.startswith("0000"):
                reserva["estado_pago"] = ESTADO_PAGO_RECHAZADO
                reserva["estado_reserva"] = ESTADO_RESERVA_PENDIENTE
                reserva["pagada"] = False
                reserva["activa"] = False

                guardar_archivo(RUTA_RESERVAS, reservas)

                logger.warning(
                    f"Pago rechazado por simulacion de tarjeta invalida | reserva_id={reserva_id}"
                )

                raise HTTPException(
                    status_code=400,
                    detail="El pago fue rechazado"
                )

            reserva["estado_pago"] = ESTADO_PAGO_PAGADO
            reserva["estado_reserva"] = ESTADO_RESERVA_CONFIRMADA
            reserva["pagada"] = True
            reserva["activa"] = True
            reserva["requiere_devolucion"] = False
            reserva["monto_devolucion"] = 0
            reserva["estado_devolucion"] = ESTADO_DEVOLUCION_NO_APLICA

            guardar_archivo(RUTA_RESERVAS, reservas)

            logger.info(
                f"Pago de seña registrado correctamente | reserva_id={reserva_id} | monto_sena={reserva.get('sena')}"
            )

            return reserva

    logger.warning(f"Pago rechazado: reserva no encontrada | reserva_id={reserva_id}")
    raise HTTPException(status_code=404, detail="Reserva no encontrada")


@router.put("/{reserva_id}/cancelar")
def cancelar_reserva(
    reserva_id: int,
    datos: CancelarReservaRequest,
    usuario_id_solicitante: int = Query(...)
):
    logger.info(
        f"Intento de cancelacion de reserva | reserva_id={reserva_id} | solicitante_id={usuario_id_solicitante}"
    )

    reservas = obtener_reservas_actualizadas()
    usuario_solicitante = obtener_usuario_por_id(usuario_id_solicitante)

    if datos.motivo_cancelacion.strip() == "":
        logger.warning(
            f"Cancelacion rechazada: motivo vacio | reserva_id={reserva_id} | solicitante_id={usuario_id_solicitante}"
        )
        raise HTTPException(
            status_code=400,
            detail="Debe ingresar un motivo de cancelación"
        )

    for reserva in reservas:
        normalizar_reserva(reserva)

        if reserva["id"] == reserva_id:
            es_admin = usuario_solicitante.get("rol") == ROL_ADMINISTRADOR
            es_duenio = reserva["usuario_id"] == usuario_id_solicitante

            if not es_admin and not es_duenio:
                logger.warning(
                    f"Cancelacion rechazada por permisos | reserva_id={reserva_id} | solicitante_id={usuario_id_solicitante}"
                )
                raise HTTPException(
                    status_code=403,
                    detail="No tiene permisos para cancelar esta reserva"
                )

            if reserva["estado_reserva"] == ESTADO_RESERVA_CANCELADA:
                logger.warning(
                    f"Cancelacion rechazada: reserva ya cancelada | reserva_id={reserva_id}"
                )
                raise HTTPException(
                    status_code=400,
                    detail="La reserva ya se encuentra cancelada"
                )

            if reserva["estado_reserva"] == ESTADO_RESERVA_FINALIZADA:
                logger.warning(
                    f"Cancelacion rechazada: reserva finalizada | reserva_id={reserva_id}"
                )
                raise HTTPException(
                    status_code=400,
                    detail="No se puede cancelar una reserva finalizada"
                )

            reserva["motivo_cancelacion"] = datos.motivo_cancelacion

            mensaje, tipo_reembolso = aplicar_cancelacion_con_regla_reembolso(reserva)

            guardar_archivo(RUTA_RESERVAS, reservas)

            logger.info(
                f"Reserva cancelada correctamente | reserva_id={reserva_id} | solicitante_id={usuario_id_solicitante} | es_admin={es_admin} | tipo_reembolso={tipo_reembolso}"
            )

            return {
                "mensaje": mensaje,
                "tipo_reembolso": tipo_reembolso,
                "reserva": reserva
            }

    logger.warning(
        f"Cancelacion rechazada: reserva no encontrada | reserva_id={reserva_id}"
    )
    raise HTTPException(status_code=404, detail="Reserva no encontrada")