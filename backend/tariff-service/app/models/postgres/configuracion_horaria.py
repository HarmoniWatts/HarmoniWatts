from sqlalchemy import (
    Column, SmallInteger, String, Boolean, Text,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class ConfiguracionHoraria(Base):
    """
    Catálogo de configuraciones horarias por comercializadora.
    
    Cada configuración representa un conjunto específico de reglas
    de asignación hora → franja. Por ejemplo:
    
    - CH00: configuración con 5 franjas (F1-F5)
    - CH01: configuración con 8 franjas (F1-F8)
    - CH02: configuración con 8 franjas (variante)
    
    Estas configuraciones se asignan a mercado + nivel de tensión
    mediante la tabla `configuracion_aplicable`.
    """
    __tablename__ = 'configuracion_horaria'
    
    id_configuracion_horaria = Column(
        SmallInteger,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único de la configuración horaria'
    )
    
    cod_comercializadora = Column(
        String(20),
        ForeignKey('comercializadora.cod_comercializadora'),
        nullable=False,
        comment='Código de la comercializadora propietaria'
    )
    
    codigo = Column(
        String(30),
        nullable=False,
        comment='Código de la configuración (CH00, CH01, ..., CH09)'
    )
    
    descripcion = Column(
        Text,
        nullable=True,
        comment='Descripción de la configuración (ej. "Fila 0 del cuadro de franjas")'
    )
    
    activo = Column(
        Boolean,
        nullable=False,
        default=True,
        comment='Indica si la configuración está vigente'
    )
    
    # =====================================================
    # CONSTRAINTS
    # =====================================================
    __table_args__ = (
        UniqueConstraint(
            'cod_comercializadora',
            'codigo',
            name='uq_configuracion_horaria_comercializadora_codigo'
        ),
        # UNIQUE compuesto necesario para FK de configuracion_aplicable
        UniqueConstraint(
            'id_configuracion_horaria',
            'cod_comercializadora',
            name='uq_configuracion_horaria_id_comercializadora'
        ),
    )
    
    # =====================================================
    # RELACIONES
    # =====================================================
    comercializadora = relationship(
        "Comercializadora",
        backref="configuraciones_horarias"
    )
    
    configuraciones_franja = relationship(
        "ConfiguracionFranja",
        back_populates="configuracion_horaria",
        cascade="all, delete-orphan"
    )
    
    configuraciones_hora = relationship(
        "ConfiguracionHora",
        back_populates="configuracion_horaria",
        cascade="all, delete-orphan"
    )
    
    configuraciones_aplicables = relationship(
        "ConfiguracionAplicable",
        back_populates="configuracion_horaria"
    )
    
    periodos_tarifarios = relationship(
        "PeriodoTarifario",
        back_populates="configuracion_horaria"
    )
    
    def __repr__(self) -> str:
        return (
            f"<ConfiguracionHoraria("
            f"id={self.id_configuracion_horaria}, "
            f"codigo='{self.codigo}', "
            f"comercializadora='{self.cod_comercializadora}')>"
        )