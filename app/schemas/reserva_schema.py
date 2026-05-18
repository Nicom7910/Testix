from pydantic import BaseModel
from datetime import date, time


class ReservaCreate(BaseModel):
    usuario_id: int
    cancha_id: int
    fecha: date
    hora_inicio: time
    hora_fin: time


class PagoReservaRequest(BaseModel):
    numero_tarjeta: str
    nombre_titular: str
    vencimiento: str
    codigo_seguridad: str


class ReservaResponse(BaseModel):
    id: int
    usuario_id: int
    cancha_id: int
    fecha: str
    hora_inicio: str
    hora_fin: str
    cantidad_horas: float
    monto_total: float
    sena: float
    activa: bool
    pagada: bool
    motivo_cancelacion: str | None = None


class CancelarReservaRequest(BaseModel):
    motivo_cancelacion: str