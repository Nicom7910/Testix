from fastapi import APIRouter, HTTPException, Query
import hashlib
import secrets

from app.schemas.usuario_schema import (
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioResponse,
    LoginRequest
)
from app.utils.file_manager import (
    leer_archivo,
    guardar_archivo,
    obtener_siguiente_id
)
from app.utils.logger import logger


router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"]
)

RUTA_USUARIOS = "app/data/usuarios.json"


def crear_hash_password(password: str) -> str:
    salt = secrets.token_hex(16)

    hash_password = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000
    ).hex()

    return f"pbkdf2_sha256${salt}${hash_password}"


def verificar_password(password_ingresada: str, password_guardada: str) -> bool:
    """
    Soporta dos casos:
    1. Contraseñas nuevas hasheadas.
    2. Contraseñas viejas en texto plano, para no romper usuarios existentes.
    """

    if password_guardada.startswith("pbkdf2_sha256$"):
        try:
            _, salt, hash_guardado = password_guardada.split("$")

            hash_ingresado = hashlib.pbkdf2_hmac(
                "sha256",
                password_ingresada.encode("utf-8"),
                salt.encode("utf-8"),
                100000
            ).hex()

            return secrets.compare_digest(hash_ingresado, hash_guardado)
        except Exception as error:
            logger.error(f"Error al verificar password hasheada: {str(error)}")
            return False

    return password_ingresada == password_guardada


def normalizar_usuario(usuario: dict):
    if "apellido" not in usuario:
        usuario["apellido"] = ""

    if "telefono" not in usuario:
        usuario["telefono"] = ""

    if "activo" not in usuario:
        usuario["activo"] = True

    if "rol" not in usuario:
        usuario["rol"] = "COMUN"

    return usuario


def validar_administrador(admin_id: int):
    logger.info(f"Validando permisos de administrador | admin_id={admin_id}")

    usuarios = leer_archivo(RUTA_USUARIOS)

    for usuario in usuarios:
        normalizar_usuario(usuario)

        if usuario["id"] == admin_id:
            if usuario["activo"] != True:
                logger.warning(
                    f"Intento de acción administrativa con usuario dado de baja | admin_id={admin_id}"
                )
                raise HTTPException(
                    status_code=403,
                    detail="El usuario administrador está dado de baja"
                )

            if usuario["rol"] != "ADMINISTRADOR":
                logger.warning(
                    f"Acceso administrativo rechazado por rol insuficiente | usuario_id={admin_id} | rol={usuario['rol']}"
                )
                raise HTTPException(
                    status_code=403,
                    detail="No tiene permisos de administrador"
                )

            logger.info(f"Permisos de administrador validados correctamente | admin_id={admin_id}")
            return usuario

    logger.warning(f"Administrador no encontrado | admin_id={admin_id}")
    raise HTTPException(
        status_code=404,
        detail="Administrador no encontrado"
    )


@router.post("/", response_model=UsuarioResponse)
def crear_usuario(usuario: UsuarioCreate):
    logger.info(f"Intento de registro de usuario | email={usuario.email}")

    usuarios = leer_archivo(RUTA_USUARIOS)

    for u in usuarios:
        normalizar_usuario(u)

        if u["email"] == usuario.email:
            logger.warning(f"Registro rechazado: email ya existente | email={usuario.email}")
            raise HTTPException(
                status_code=400,
                detail="Ya existe un usuario con ese email"
            )

    nuevo_usuario = {
        "id": obtener_siguiente_id(usuarios),
        "nombre": usuario.nombre,
        "apellido": usuario.apellido,
        "email": usuario.email,
        "telefono": usuario.telefono,
        "password": crear_hash_password(usuario.password),
        "rol": usuario.rol,
        "activo": True
    }

    usuarios.append(nuevo_usuario)
    guardar_archivo(RUTA_USUARIOS, usuarios)

    logger.info(
        f"Usuario registrado correctamente | usuario_id={nuevo_usuario['id']} | email={nuevo_usuario['email']} | rol={nuevo_usuario['rol']}"
    )

    return nuevo_usuario


@router.get("/", response_model=list[UsuarioResponse])
def listar_usuarios(admin_id: int = Query(...)):
    logger.info(f"Solicitud de listado de usuarios | admin_id={admin_id}")

    validar_administrador(admin_id)

    usuarios = leer_archivo(RUTA_USUARIOS)
    usuarios_normalizados = []

    for usuario in usuarios:
        usuarios_normalizados.append(normalizar_usuario(usuario))

    logger.info(
        f"Listado de usuarios generado correctamente | admin_id={admin_id} | cantidad={len(usuarios_normalizados)}"
    )

    return usuarios_normalizados


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def obtener_usuario(
    usuario_id: int,
    usuario_id_solicitante: int = Query(...)
):
    logger.info(
        f"Solicitud de consulta de usuario | usuario_id={usuario_id} | solicitante_id={usuario_id_solicitante}"
    )

    usuarios = leer_archivo(RUTA_USUARIOS)
    usuario_solicitante = None

    for usuario in usuarios:
        normalizar_usuario(usuario)

        if usuario["id"] == usuario_id_solicitante:
            usuario_solicitante = usuario

    if usuario_solicitante is None:
        logger.warning(
            f"Consulta rechazada: usuario solicitante no encontrado | solicitante_id={usuario_id_solicitante}"
        )
        raise HTTPException(
            status_code=404,
            detail="Usuario solicitante no encontrado"
        )

    if (
        usuario_solicitante["rol"] != "ADMINISTRADOR"
        and usuario_solicitante["id"] != usuario_id
    ):
        logger.warning(
            f"Consulta rechazada por permisos | usuario_id={usuario_id} | solicitante_id={usuario_id_solicitante}"
        )
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para consultar este usuario"
        )

    for usuario in usuarios:
        normalizar_usuario(usuario)

        if usuario["id"] == usuario_id:
            logger.info(
                f"Usuario consultado correctamente | usuario_id={usuario_id} | solicitante_id={usuario_id_solicitante}"
            )
            return usuario

    logger.warning(f"Usuario no encontrado | usuario_id={usuario_id}")
    raise HTTPException(status_code=404, detail="Usuario no encontrado")


@router.put("/{usuario_id}", response_model=UsuarioResponse)
def modificar_usuario(
    usuario_id: int,
    datos_usuario: UsuarioUpdate,
    usuario_id_solicitante: int = Query(...)
):
    logger.info(
        f"Intento de modificación de usuario | usuario_id={usuario_id} | solicitante_id={usuario_id_solicitante}"
    )

    usuarios = leer_archivo(RUTA_USUARIOS)
    usuario_solicitante = None

    for usuario in usuarios:
        normalizar_usuario(usuario)

        if usuario["id"] == usuario_id_solicitante:
            usuario_solicitante = usuario

    if usuario_solicitante is None:
        logger.warning(
            f"Modificación rechazada: usuario solicitante no encontrado | solicitante_id={usuario_id_solicitante}"
        )
        raise HTTPException(
            status_code=404,
            detail="Usuario solicitante no encontrado"
        )

    if (
        usuario_solicitante["rol"] != "ADMINISTRADOR"
        and usuario_solicitante["id"] != usuario_id
    ):
        logger.warning(
            f"Modificación rechazada por permisos | usuario_id={usuario_id} | solicitante_id={usuario_id_solicitante}"
        )
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para modificar este usuario"
        )

    for u in usuarios:
        normalizar_usuario(u)

        if u["email"] == datos_usuario.email and u["id"] != usuario_id:
            logger.warning(
                f"Modificación rechazada: email en uso | usuario_id={usuario_id} | email={datos_usuario.email}"
            )
            raise HTTPException(
                status_code=400,
                detail="El email ya está en uso"
            )

    for usuario in usuarios:
        normalizar_usuario(usuario)

        if usuario["id"] == usuario_id:
            usuario["nombre"] = datos_usuario.nombre
            usuario["apellido"] = datos_usuario.apellido
            usuario["email"] = datos_usuario.email
            usuario["telefono"] = datos_usuario.telefono

            if datos_usuario.password.startswith("pbkdf2_sha256$"):
                usuario["password"] = datos_usuario.password
            else:
                usuario["password"] = crear_hash_password(datos_usuario.password)

            if usuario_solicitante["rol"] == "ADMINISTRADOR":
                usuario["rol"] = datos_usuario.rol
                usuario["activo"] = datos_usuario.activo

            guardar_archivo(RUTA_USUARIOS, usuarios)

            logger.info(
                f"Usuario modificado correctamente | usuario_id={usuario_id} | solicitante_id={usuario_id_solicitante}"
            )

            return usuario

    logger.warning(f"Modificación rechazada: usuario no encontrado | usuario_id={usuario_id}")
    raise HTTPException(status_code=404, detail="Usuario no encontrado")


@router.delete("/{usuario_id}")
def dar_baja_usuario(
    usuario_id: int,
    admin_id: int = Query(...)
):
    logger.info(
        f"Intento de baja de usuario | usuario_id={usuario_id} | admin_id={admin_id}"
    )

    validar_administrador(admin_id)

    usuarios = leer_archivo(RUTA_USUARIOS)

    for usuario in usuarios:
        normalizar_usuario(usuario)

        if usuario["id"] == usuario_id:
            usuario["activo"] = False
            guardar_archivo(RUTA_USUARIOS, usuarios)

            logger.info(
                f"Usuario dado de baja correctamente | usuario_id={usuario_id} | admin_id={admin_id}"
            )

            return {
                "mensaje": "Usuario dado de baja correctamente",
                "usuario": usuario
            }

    logger.warning(
        f"Baja rechazada: usuario no encontrado | usuario_id={usuario_id} | admin_id={admin_id}"
    )
    raise HTTPException(status_code=404, detail="Usuario no encontrado")


@router.post("/login")
def login(datos: LoginRequest):
    logger.info(f"Intento de login | email={datos.email}")

    usuarios = leer_archivo(RUTA_USUARIOS)
    hubo_cambios = False

    for usuario in usuarios:
        normalizar_usuario(usuario)

        if (
            usuario["email"] == datos.email
            and usuario["activo"] == True
            and verificar_password(datos.password, usuario["password"])
        ):
            if not usuario["password"].startswith("pbkdf2_sha256$"):
                usuario["password"] = crear_hash_password(datos.password)
                hubo_cambios = True

            if hubo_cambios:
                guardar_archivo(RUTA_USUARIOS, usuarios)
                logger.info(
                    f"Password migrada a hash seguro durante login | usuario_id={usuario['id']}"
                )

            logger.info(
                f"Login exitoso | usuario_id={usuario['id']} | email={usuario['email']} | rol={usuario['rol']}"
            )

            return {
                "mensaje": "Login exitoso",
                "usuario": {
                    "id": usuario["id"],
                    "nombre": usuario["nombre"],
                    "apellido": usuario.get("apellido", ""),
                    "email": usuario["email"],
                    "telefono": usuario.get("telefono", ""),
                    "rol": usuario["rol"]
                }
            }

    logger.warning(f"Login rechazado | email={datos.email}")
    raise HTTPException(
        status_code=401,
        detail="Email o contraseña incorrectos"
    )