from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.core.database import Base


class TipoCliente(Base):
    """
    Clasificación del uso del servicio eléctrico.
    
    Valores típicos:
        I - Industrial
        C - Comercial
        O - Oficial
        E - Especial
        R - Residencial
    """
    __tablename__ = 'tipo_cliente'
    
    cod_tipo_cliente = Column(String(1), primary_key=True)
    nombre = Column(String(50), nullable=False)
    descripcion = Column(String(150), nullable=False)
    
    # Relaciones
    clientes = relationship("Cliente", back_populates="tipo_cliente", lazy="selectin")
    
    def __repr__(self) -> str:
        return f"<TipoCliente(codigo='{self.cod_tipo_cliente}', nombre='{self.nombre}')>"