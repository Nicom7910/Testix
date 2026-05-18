from pydantic import BaseModel, Field


class CanchaCreate(BaseModel):
    nombre: str = Field(..., min_length=1)
    tipo_superficie: str = Field(..., min_length=1)
    techada: bool
    precio_por_hora: float = Field(..., gt=0)


class CanchaUpdate(BaseModel):
    nombre: str = Field(..., min_length=1)
    tipo_superficie: str = Field(..., min_length=1)
    techada: bool
    precio_por_hora: float = Field(..., gt=0)
    activa: bool = True


class CanchaResponse(BaseModel):
    id: int
    nombre: str
    tipo_superficie: str
    techada: bool
    precio_por_hora: float
    activa: bool