from sqlalchemy import Column, Integer, Date, Time, Boolean, ForeignKey, Float
from app.database import Base


class Reserva(Base):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, index=True)

    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    cancha_id = Column(Integer, ForeignKey("canchas.id"), nullable=False)

    fecha = Column(Date, nullable=False)
    hora = Column(Time, nullable=False)

    monto_total = Column(Float, nullable=False)
    sena = Column(Float, nullable=False)

    activa = Column(Boolean, default=True)