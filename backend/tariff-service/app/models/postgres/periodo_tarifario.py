from sqlalchemy import (
    Column, BigInteger, SmallInteger, Integer, String, Date,
    Text, TIMESTAMP, ForeignKey, ForeignKeyConstraint,
    UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class PeriodoTarifario(Base):
    """
    Versiones mensuales de tarifas con vigencia y estado.
    
    Una misma tarifa puede tener varias versiones para el mismo
    período (correcciones o republicaciones).
    """
    __tablename__ = 'periodo_tarifario'
    
    # =====================================================
    # IDENTIFICACIÓN
    # =====================================================
    id_periodo_tarifario = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )
    
    id_tarifa = Column(
        BigInteger,
        ForeignKey('tarifa.id_tarifa'),
        nullable=False
    )
    
    id_configuracion_horaria = Column(
        SmallInteger,
        ForeignKey('configuracion_horaria.id_configuracion_horaria'),
        nullable=True
    )
    
    # =====================================================
    # PERÍODO
    # =====================================================
    anio = Column(SmallInteger, nullable=False)
    mes = Column(SmallInteger, nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    
    # =====================================================
    # VERSIONADO
    # =====================================================
    numero_version = Column(Integer, nullable=False, default=1)
    
    fecha_calculo = Column(Date)
    fecha_publicacion = Column(Date)
    estado = Column(String(20), nullable=False, default='BORRADOR')
    observaciones = Column(Text)
    creada_en = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    
    # =====================================================
    # CONSTRAINTS
    # =====================================================
    __table_args__ = (
        UniqueConstraint(
            'id_tarifa', 'anio', 'mes', 'numero_version',
            name='uq_periodo_tarifario_anio_mes'
        ),
        UniqueConstraint(
            'id_periodo_tarifario', 'id_configuracion_horaria',
            name='uq_periodo_config'
        ),
        CheckConstraint('mes BETWEEN 1 AND 12', name='ck_periodo_tarifario_mes'),
        CheckConstraint('fecha_inicio <= fecha_fin', name='ck_periodo_tarifario_fechas'),
        CheckConstraint('numero_version > 0', name='ck_version_tarifa_numero'),
        CheckConstraint(
            "estado IN ('BORRADOR', 'PUBLICADA', 'SUPERADA', 'ANULADA')",
            name='ck_version_tarifa_estado'
        ),
    )
    
    # =====================================================
    # RELACIONES — TODAS las que faltaban
    # =====================================================
    
    # Relación con Tarifa (inversa)
    tarifa = relationship(
        "Tarifa",
        back_populates="periodos",
        foreign_keys=[id_tarifa]
    )
    
    # ⚠️ ESTA ERA LA QUE FALTABA
    configuracion_horaria = relationship(
        "ConfiguracionHoraria",
        back_populates="periodos_tarifarios",
        foreign_keys=[id_configuracion_horaria]
    )
    
    # Valores por franja o monomia
    valores = relationship(
        "TarifaValor",
        back_populates="periodo",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # Componentes del CU (G, T, D, Cv, PR, R)
    componentes = relationship(
        "ComponenteValorMes",
        back_populates="periodo",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # =====================================================
    # REPRESENTACIÓN
    # =====================================================
    def __repr__(self) -> str:
        return (
            f"<PeriodoTarifario(id={self.id_periodo_tarifario}, "
            f"anio={self.anio}, mes={self.mes}, "
            f"version={self.numero_version}, "
            f"estado='{self.estado}')>"
        )