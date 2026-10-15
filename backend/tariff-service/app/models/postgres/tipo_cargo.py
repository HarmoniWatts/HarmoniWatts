from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.core.database import Base


class TipoCargo(Base):
    """
    Catálogo que define la dimensión matemática y la unidad de medida
    de cada concepto tarifario.
    
    Ejemplos:
        VARIABLE_ENERGIA  - COP/kWh
        CFMJ_CREG         - COP/mes
        DEMANDA_POTENCIA  - COP/kW-mes
        CONEXION_DIA      - COP/día
    """
    __tablename__ = 'tipo_cargo'
    
    cod_tipo_cargo = Column(String(30), primary_key=True)
    nombre = Column(String(100), nullable=False)
    unidad = Column(String(20), nullable=False)
    
    # Relaciones
    componentes_costo = relationship("ComponenteCosto", back_populates="tipo_cargo")
    
    def __repr__(self) -> str:
        return f"<TipoCargo(codigo='{self.cod_tipo_cargo}', unidad='{self.unidad}')>"