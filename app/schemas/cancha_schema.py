from pydantic import BaseModel


class CanchaCreate(BaseModel):
    nombre: str
    tipo_superficie: str
    techada: bool
    precio_por_hora: float
    precio_diurno: float | None = None
    precio_nocturno: float | None = None


class CanchaUpdate(BaseModel):
    nombre: str
    tipo_superficie: str
    techada: bool
    precio_por_hora: float
    activa: bool
    precio_diurno: float | None = None
    precio_nocturno: float | None = None


class CanchaResponse(BaseModel):
    id: int
    nombre: str
    tipo_superficie: str
    techada: bool
    precio_por_hora: float
    activa: bool
    precio_diurno: float | None = None
    precio_nocturno: float | None = None