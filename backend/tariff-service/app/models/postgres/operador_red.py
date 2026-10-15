from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class OperadorRed(Base):
    """
    Empresa propietaria o administradora del Sistema de Distribución Local (SDL).
    """
    __tablename__ = 'operador_red'
    
    cod_or = Column(String(20), primary_key=True)
    nombre_operador = Column(String(100), nullable=False, unique=True)
    nit = Column(String(20), nullable=True)
    descripcion = Column(Text)
    activo = Column(Boolean, default=True)
    
    # Relaciones
    mercados_red = relationship("MercadoRed", back_populates="operador_red")
    
    def __repr__(self) -> str:
        return f"<OperadorRed(codigo='{self.cod_or}', nombre='{self.nombre_operador}')>"