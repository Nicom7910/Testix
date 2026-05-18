from pydantic import BaseModel, Field, EmailStr
from typing import Literal


class UsuarioCreate(BaseModel):
    nombre: str = Field(..., min_length=1)
    apellido: str = Field(..., min_length=1)
    email: EmailStr
    telefono: str = Field(..., min_length=1)
    password: str = Field(..., min_length=4)
    rol: Literal["COMUN", "ADMINISTRADOR"] = "COMUN"


class UsuarioUpdate(BaseModel):
    nombre: str = Field(..., min_length=1)
    apellido: str = Field(..., min_length=1)
    email: EmailStr
    telefono: str = Field(..., min_length=1)
    password: str = Field(..., min_length=4)
    rol: Literal["COMUN", "ADMINISTRADOR"]
    activo: bool = True


class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: EmailStr
    telefono: str
    rol: str
    activo: bool


class LoginRequest(BaseModel):
    email: EmailStr
    password: str