# app/models/postgres/tarifa_valor.py

from sqlalchemy import (
    Column, BigInteger, SmallInteger, Numeric, String,
    ForeignKey, CheckConstraint
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class TarifaValor(Base):
    __tablename__ = 'tarifa_valor'
    
    id_tarifa_valor = Column(BigInteger, primary_key=True, autoincrement=True)
    
    id_periodo_tarifario = Column(
        BigInteger,
        ForeignKey(
            'periodo_tarifario.id_periodo_tarifario',
            name='fk_tv_periodo'
        ),
        nullable=False
    )
    
    id_configuracion_horaria = Column(SmallInteger, nullable=True)
    
    id_franja_horaria = Column(
        SmallInteger,
        ForeignKey(
            'franja_horaria.id_franja_horaria',
            name='fk_tv_franja_horaria'
        ),
        nullable=True
    )
    
    valor = Column(Numeric(18, 6), nullable=False)
    unidad = Column(String(30), nullable=False, default='COP/kWh')
    
    __table_args__ = (
        CheckConstraint('valor >= 0', name='ck_valor_positivo'),
        CheckConstraint(
            '(id_configuracion_horaria IS NULL) = (id_franja_horaria IS NULL)',
            name='ck_tv_config_franja'
        ),
    )
    
    # =====================================================
    # RELACIONES — solo la que NO tiene conflicto
    # =====================================================
    periodo = relationship(
        "PeriodoTarifario",
        back_populates="valores",
        foreign_keys=[id_periodo_tarifario]
    )
    
    # ⚠️ ELIMINADA — conflicto con FK compuesta:
    # franja = relationship("FranjaHoraria", ...)
    
    def __repr__(self) -> str:
        return f"<TarifaValor(id={self.id_tarifa_valor}, valor={self.valor})>"