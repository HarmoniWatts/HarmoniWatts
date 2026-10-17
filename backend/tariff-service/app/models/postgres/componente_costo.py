from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class ComponenteCosto(Base):
    """
    Catálogo maestro de componentes del Costo Unitario de Prestación
    del Servicio (CU) y Costo Fijo.
    
    Componentes típicos:
        Gm   - Generación
        Tm   - Transmisión
        Dm   - Distribución
        Cm   - Comercialización
        PRm  - Pérdidas
        Rm   - Restricciones
        COT  - Costo de Opción Tarifaria
        Cfmj - Costo Fijo de Comercialización
    """
    __tablename__ = 'componente_costo'
    
    cod_componente = Column(String(15), primary_key=True)
    nombre = Column(String(100), nullable=False)
    cod_tipo_cargo = Column(
        String(30),
        ForeignKey('tipo_cargo.cod_tipo_cargo'),
        nullable=False
    )
    descripcion = Column(Text)
    
    # Relaciones
    tipo_cargo = relationship("TipoCargo", back_populates="componentes_costo")
    valores_mes = relationship("ComponenteValorMes", back_populates="componente")
    
    def __repr__(self) -> str:
        return f"<ComponenteCosto(codigo='{self.cod_componente}', nombre='{self.nombre}')>"