from sqlalchemy import Column, BigInteger, SmallInteger, Numeric, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class TarifaValor(Base):
    __tablename__ = 'tarifa_valor'
    
    id_tarifa_valor = Column(BigInteger, primary_key=True)
    id_periodo_tarifario = Column(BigInteger, ForeignKey('periodo_tarifario.id_periodo_tarifario'), nullable=False)
    id_configuracion_horaria = Column(SmallInteger, ForeignKey('configuracion_horaria.id_configuracion_horaria'))
    id_franja_horaria = Column(SmallInteger, ForeignKey('franja_horaria.id_franja_horaria'))
    valor = Column(Numeric(18, 6), nullable=False)
    unidad = Column(String(30), nullable=False, default='COP/kWh')
    
    # Relaciones
    periodo = relationship("PeriodoTarifario", back_populates="valores")
    franja = relationship("FranjaHoraria")