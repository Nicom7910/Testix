from fastapi import APIRouter, HTTPException

from app.schemas.usuario_schema import (
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioResponse,
    LoginRequest
)

from app.utils.file_manager import leer_archivo, guardar_archivo, obtener_siguiente_id

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"]
)

RUTA_USUARIOS = "app/data/usuarios.json"


@router.post("/", response_model=UsuarioResponse)
def crear_usuario(usuario: UsuarioCreate):
    usuarios = leer_archivo(RUTA_USUARIOS)

    for u in usuarios:
        if u["email"] == usuario.email:
            raise HTTPException(
                status_code=400,
                detail="Ya existe un usuario con ese email"
            )

    nuevo_usuario = {
        "id": obtener_siguiente_id(usuarios),
        "nombre": usuario.nombre,
        "email": usuario.email,
        "password": usuario.password,
        "rol": usuario.rol,
        "activo": True
    }

    usuarios.append(nuevo_usuario)
    guardar_archivo(RUTA_USUARIOS, usuarios)

    return nuevo_usuario


@router.get("/", response_model=list[UsuarioResponse])
def listar_usuarios():
    usuarios = leer_archivo(RUTA_USUARIOS)
    return usuarios


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def obtener_usuario(usuario_id: int):
    usuarios = leer_archivo(RUTA_USUARIOS)

    for usuario in usuarios:
        if usuario["id"] == usuario_id:
            return usuario

    raise HTTPException(status_code=404, detail="Usuario no encontrado")


@router.put("/{usuario_id}", response_model=UsuarioResponse)
def modificar_usuario(usuario_id: int, datos_usuario: UsuarioUpdate):
    usuarios = leer_archivo(RUTA_USUARIOS)

    for u in usuarios:
        if u["email"] == datos_usuario.email and u["id"] != usuario_id:
            raise HTTPException(
                status_code=400,
                detail="El email ya está en uso"
            )

    for usuario in usuarios:
        if usuario["id"] == usuario_id:
            usuario["nombre"] = datos_usuario.nombre
            usuario["email"] = datos_usuario.email
            usuario["password"] = datos_usuario.password
            usuario["rol"] = datos_usuario.rol
            usuario["activo"] = datos_usuario.activo

            guardar_archivo(RUTA_USUARIOS, usuarios)
            return usuario

    raise HTTPException(status_code=404, detail="Usuario no encontrado")


@router.delete("/{usuario_id}")
def dar_baja_usuario(usuario_id: int):
    usuarios = leer_archivo(RUTA_USUARIOS)

    for usuario in usuarios:
        if usuario["id"] == usuario_id:
            usuario["activo"] = False
            guardar_archivo(RUTA_USUARIOS, usuarios)

            return {
                "mensaje": "Usuario dado de baja correctamente",
                "usuario": usuario
            }

    raise HTTPException(status_code=404, detail="Usuario no encontrado")


@router.post("/login")
def login(datos: LoginRequest):
    usuarios = leer_archivo(RUTA_USUARIOS)

    for usuario in usuarios:
        if (
            usuario["email"] == datos.email
            and usuario["password"] == datos.password
            and usuario["activo"] == True
        ):
            return {
                "mensaje": "Login exitoso",
                "usuario": {
                    "id": usuario["id"],
                    "nombre": usuario["nombre"],
                    "email": usuario["email"],
                    "rol": usuario["rol"]
                }
            }

    raise HTTPException(
        status_code=401,
        detail="Email o contraseña incorrectos"
    )