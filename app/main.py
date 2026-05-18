from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.cancha_routes import router as cancha_router
from app.routes.usuario_routes import router as usuario_router
from app.routes.reserva_routes import router as reserva_router

app = FastAPI(
    title="API Reserva de Canchas de Tenis",
    description="Sistema con FastAPI y persistencia en archivos JSON",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cancha_router)
app.include_router(usuario_router)
app.include_router(reserva_router)


@app.get("/")
def inicio():
    return {
        "mensaje": "API funcionando correctamente con archivos JSON"
    }