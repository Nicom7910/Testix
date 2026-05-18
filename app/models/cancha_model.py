from sqlalchemy import Column, Integer, String, Boolean, Float
from app.database import Base


class Cancha(Base):
    __tablename__ = "canchas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    tipo_superficie = Column(String, nullable=False)
    techada = Column(Boolean, default=False)
    precio_por_hora = Column(Float, nullable=False)
    activa = Column(Boolean, default=True)