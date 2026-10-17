from sqlalchemy import Column, String, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class MercadoRed(Base):
    """
    Mercados de comercialización delimitados por la infraestructura
    del Operador de Red.
    """
    __tablename__ = 'mercado_red'
    
    cod_mercado = Column(String(30), primary_key=True)
    nombre_mercado = Column(String(100), nullable=False)
    cod_or = Column(String(20), ForeignKey('operador_red.cod_or'), nullable=False)
    descripcion = Column(Text)
    activo = Column(Boolean, default=True)
    
    # Relaciones
    operador_red = relationship("OperadorRed", back_populates="mercados_red")
    mercados_zona = relationship("MercadoZona", back_populates="mercado_red")
    configuraciones_aplicables = relationship(
        "ConfiguracionAplicable",
        back_populates="mercado_red"
    )
    
    def __repr__(self) -> str:
        return f"<MercadoRed(codigo='{self.cod_mercado}', nombre='{self.nombre_mercado}')>"