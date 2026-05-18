from pydantic import BaseModel
from datetime import date, time


class ReservaCreate(BaseModel):
    usuario_id: int
    cancha_id: int
    fecha: date
    hora: time


class ReservaResponse(BaseModel):
    id: int
    usuario_id: int
    cancha_id: int
    fecha: str
    hora: str
    monto_total: float
    sena: float
    activa: bool