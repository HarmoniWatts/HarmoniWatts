from sqlalchemy import Column, BigInteger, String, Boolean, TIMESTAMP, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Tarifa(Base):
    __tablename__ = 'tarifa'
    
    id_tarifa = Column(BigInteger, primary_key=True)
    cod_comercializadora = Column(String(20), nullable=False)
    cod_mercado = Column(String(30), nullable=False)
    cod_nivel = Column(String(15), nullable=False)
    cod_tipo_tarifa = Column(String(20))
    codigo_tarifa = Column(String(50), unique=True)
    nombre_tarifa = Column(String(200))
    estrato = Column(String(5))
    resolucion_regulatoria = Column(String(100))
    activa = Column(Boolean, default=True)
    fecha_registro = Column(TIMESTAMP, server_default=func.now())
    
    # Relaciones
    periodos = relationship("PeriodoTarifario", back_populates="tarifa")