from sqlalchemy import Column, SmallInteger, String, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base


class ZonaGeografica(Base):
    """
    Catálogo geográfico: municipios y sus características.
    
    El campo `altura` es clave para el cálculo del Consumo de Subsistencia (CS):
        < 1000 m.s.n.m.  → CS = 173 kWh/mes
        >= 1000 m.s.n.m. → CS = 130 kWh/mes
    """
    __tablename__ = 'zona_geografica'
    
    id_zona = Column(SmallInteger, primary_key=True, autoincrement=True)
    nombre_zona = Column(String(50), nullable=False)
    municipio = Column(String(50))
    departamento = Column(String(50))
    region = Column(String(50))
    altura = Column(Integer, comment='Altura sobre el nivel del mar en metros')
    
    # Relaciones
    mercados_zona = relationship("MercadoZona", back_populates="zona_geografica")
    
    def __repr__(self) -> str:
        return (
            f"<ZonaGeografica(id={self.id_zona}, "
            f"municipio='{self.municipio}', altura={self.altura})>"
        )