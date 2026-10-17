from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class NivelTension(Base):
    """
    Niveles de tensión del sistema de distribución (CREG).
    
    Valores típicos:
        N1_1      - Nivel 1.1
        N1_2      - Nivel 1.2
        N1_2_50   - Nivel 1.2* - 50%
        N2        - Nivel 2
        N3        - Nivel 3
        N4        - Nivel 4
    """
    __tablename__ = 'nivel_tension'
    
    cod_nivel = Column(String(15), primary_key=True)
    nombre = Column(String(50), nullable=False)
    descripcion = Column(Text)
    activo = Column(Boolean, nullable=False, default=True)
    
    # Relaciones
    clientes = relationship("Cliente", back_populates="nivel_tension")
    
    configuraciones_aplicables = relationship(
        "ConfiguracionAplicable",
        back_populates="nivel_tension",
        foreign_keys="ConfiguracionAplicable.cod_nivel",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<NivelTension(codigo='{self.cod_nivel}', nombre='{self.nombre}')>"