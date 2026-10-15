# app/models/postgres/franja_horaria.py

from sqlalchemy import (
    Column, SmallInteger, String, Boolean,
    ForeignKey, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class FranjaHoraria(Base):
    __tablename__ = 'franja_horaria'
    
    id_franja_horaria = Column(SmallInteger, primary_key=True, autoincrement=True)
    cod_comercializadora = Column(
        String(20),
        ForeignKey('comercializadora.cod_comercializadora'),
        nullable=False
    )
    codigo = Column(String(30), nullable=False)
    tipo_dia = Column(String(10), nullable=False, default='TODOS')
    activo = Column(Boolean, nullable=False, default=True)
    
    __table_args__ = (
        UniqueConstraint(
            'cod_comercializadora', 'codigo', 'tipo_dia',
            name='uq_franja_comercializadora_tipo_dia'
        ),
        CheckConstraint(
            "tipo_dia IN ('TODOS', 'LABORAL', 'SABADO', 'DOMINGO', 'FESTIVO')",
            name='ck_tipo_dia'
        ),
    )
    
    # =====================================================
    # RELACIONES — solo las que NO tienen FK compuesta
    # =====================================================
    comercializadora = relationship(
        "Comercializadora",
        back_populates="franjas_horarias"
    )
    
    configuraciones_franja = relationship(
        "ConfiguracionFranja",
        back_populates="franja_horaria",
        cascade="all, delete-orphan"
    )
    
    # ⚠️ ELIMINADAS — conflicto con FK compuesta:
    # configuraciones_hora = relationship("ConfiguracionHora", ...)
    # tarifas_valor = relationship("TarifaValor", ...)
    
    def __repr__(self) -> str:
        return f"<FranjaHoraria(id={self.id_franja_horaria}, codigo='{self.codigo}')>"