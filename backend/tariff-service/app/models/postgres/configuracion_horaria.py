# app/models/postgres/configuracion_horaria.py

from sqlalchemy import (
    Column, SmallInteger, String, Boolean, Text,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class ConfiguracionHoraria(Base):
    __tablename__ = 'configuracion_horaria'
    
    id_configuracion_horaria = Column(SmallInteger, primary_key=True, autoincrement=True)
    cod_comercializadora = Column(
        String(20),
        ForeignKey('comercializadora.cod_comercializadora'),
        nullable=False
    )
    codigo = Column(String(30), nullable=False)
    descripcion = Column(Text)
    activo = Column(Boolean, nullable=False, default=True)
    
    __table_args__ = (
        UniqueConstraint(
            'cod_comercializadora', 'codigo',
            name='uq_configuracion_horaria_comercializadora_codigo'
        ),
        UniqueConstraint(
            'id_configuracion_horaria', 'cod_comercializadora',
            name='uq_configuracion_horaria_id_comercializadora'
        ),
    )
    
    # =====================================================
    # RELACIONES — solo las que NO tienen conflicto
    # =====================================================
    comercializadora = relationship(
        "Comercializadora",
        back_populates="configuraciones_horarias"
    )
    
    configuraciones_franja = relationship(
        "ConfiguracionFranja",
        back_populates="configuracion_horaria",
        cascade="all, delete-orphan"
    )
    
    configuraciones_aplicables = relationship(
        "ConfiguracionAplicable",
        back_populates="configuracion_horaria",
        foreign_keys="ConfiguracionAplicable.id_configuracion_horaria"
    )
    
    periodos_tarifarios = relationship(
        "PeriodoTarifario",
        back_populates="configuracion_horaria",
        foreign_keys="PeriodoTarifario.id_configuracion_horaria"
    )
    
    # ⚠️ ELIMINADA — conflicto con FK compuesta:
    # configuraciones_hora = relationship("ConfiguracionHora", ...)
    
    def __repr__(self) -> str:
        return (
            f"<ConfiguracionHoraria(id={self.id_configuracion_horaria}, "
            f"codigo='{self.codigo}')>"
        )