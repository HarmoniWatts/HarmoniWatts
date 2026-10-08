from sqlalchemy import Column, BigInteger, String, SmallInteger, Integer, Date, TIMESTAMP, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class PeriodoTarifario(Base):
    __tablename__ = 'periodo_tarifario'
    
    id_periodo_tarifario = Column(BigInteger, primary_key=True)
    id_tarifa = Column(BigInteger, ForeignKey('tarifa.id_tarifa'), nullable=False)
    id_configuracion_horaria = Column(SmallInteger, ForeignKey('configuracion_horaria.id_configuracion_horaria'))
    anio = Column(SmallInteger, nullable=False)
    mes = Column(SmallInteger, nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    numero_version = Column(Integer, nullable=False)
    fecha_calculo = Column(Date)
    fecha_publicacion = Column(Date)
    estado = Column(String(20), nullable=False, default='BORRADOR')
    observaciones = Column(Text)
    creada_en = Column(TIMESTAMP, server_default='CURRENT_TIMESTAMP')
    
    # Relaciones
    tarifa = relationship("Tarifa", back_populates="periodos")
    valores = relationship("TarifaValor", back_populates="periodo")
    componentes = relationship("ComponenteValorMes", back_populates="periodo")