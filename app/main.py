from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import usuario_routes
from app.routes import cancha_routes
from app.routes import reserva_routes
from app.routes import reporte_routes

app = FastAPI(
    title="Sistema de Gestión de Alquiler de Canchas de Tenis",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(usuario_routes.router)
app.include_router(cancha_routes.router)
app.include_router(reserva_routes.router)
app.include_router(reporte_routes.router)


@app.get("/")
def inicio():
    return {
        "mensaje": "API del Sistema de Gestión de Alquiler de Canchas de Tenis"
    }