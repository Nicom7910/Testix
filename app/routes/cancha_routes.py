from fastapi import APIRouter, HTTPException

from app.schemas.cancha_schema import CanchaCreate, CanchaUpdate, CanchaResponse
from app.utils.file_manager import leer_archivo, guardar_archivo, obtener_siguiente_id

router = APIRouter(
    prefix="/canchas",
    tags=["Canchas"]
)

RUTA_CANCHAS = "app/data/canchas.json"


@router.post("/", response_model=CanchaResponse)
def crear_cancha(cancha: CanchaCreate):
    canchas = leer_archivo(RUTA_CANCHAS)

    nueva_cancha = {
        "id": obtener_siguiente_id(canchas),
        "nombre": cancha.nombre,
        "tipo_superficie": cancha.tipo_superficie,
        "techada": cancha.techada,
        "precio_por_hora": cancha.precio_por_hora,
        "activa": True
    }

    canchas.append(nueva_cancha)
    guardar_archivo(RUTA_CANCHAS, canchas)

    return nueva_cancha


@router.get("/", response_model=list[CanchaResponse])
def listar_canchas():
    canchas = leer_archivo(RUTA_CANCHAS)
    return canchas


@router.get("/disponibles", response_model=list[CanchaResponse])
def listar_canchas_disponibles():
    canchas = leer_archivo(RUTA_CANCHAS)

    disponibles = []

    for cancha in canchas:
        if cancha["activa"] == True:
            disponibles.append(cancha)

    return disponibles


@router.get("/{cancha_id}", response_model=CanchaResponse)
def obtener_cancha(cancha_id: int):
    canchas = leer_archivo(RUTA_CANCHAS)

    for cancha in canchas:
        if cancha["id"] == cancha_id:
            return cancha

    raise HTTPException(status_code=404, detail="Cancha no encontrada")


@router.put("/{cancha_id}", response_model=CanchaResponse)
def modificar_cancha(cancha_id: int, datos_cancha: CanchaUpdate):
    canchas = leer_archivo(RUTA_CANCHAS)

    for cancha in canchas:
        if cancha["id"] == cancha_id:
            cancha["nombre"] = datos_cancha.nombre
            cancha["tipo_superficie"] = datos_cancha.tipo_superficie
            cancha["techada"] = datos_cancha.techada
            cancha["precio_por_hora"] = datos_cancha.precio_por_hora
            cancha["activa"] = datos_cancha.activa

            guardar_archivo(RUTA_CANCHAS, canchas)
            return cancha

    raise HTTPException(status_code=404, detail="Cancha no encontrada")


@router.delete("/{cancha_id}")
def dar_baja_cancha(cancha_id: int):
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
def modificar_precio_cancha(cancha_id: int, precio_por_hora: float):
    canchas = leer_archivo(RUTA_CANCHAS)

    if precio_por_hora <= 0:
        raise HTTPException(
            status_code=400,
            detail="El precio por hora debe ser mayor a 0"
        )

    for cancha in canchas:
        if cancha["id"] == cancha_id:
            cancha["precio_por_hora"] = precio_por_hora
            guardar_archivo(RUTA_CANCHAS, canchas)

            return {
                "mensaje": "Precio actualizado correctamente",
                "cancha": cancha
            }

    raise HTTPException(status_code=404, detail="Cancha no encontrada")