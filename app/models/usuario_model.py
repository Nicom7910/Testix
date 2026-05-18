from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)
    rol = Column(String, nullable=False, default="COMUN")
    activo = Column(Boolean, default=True)