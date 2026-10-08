from sqlalchemy import Column, SmallInteger, String, Boolean, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class FranjaHoraria(Base):
    """
    Catálogo de franjas horarias por comercializadora.
    
    Define qué franjas existen (F1..F8) para cada comercializadora
    y para qué tipo de día aplican (TODOS, LABORAL, SÁBADO, DOMINGO, FESTIVO).
    
    Ejemplo:
        ('ENERTOTAL', 'F1', 'TODOS', TRUE)
        ('ENERTOTAL', 'F2', 'TODOS', TRUE)
        ...
        ('ENERTOTAL', 'F8', 'TODOS', TRUE)
    """
    __tablename__ = 'franja_horaria'
    
    id_franja_horaria = Column(
        SmallInteger,
        primary_key=True,
        autoincrement=True
    )
    
    cod_comercializadora = Column(
        String(30),
        ForeignKey('comercializadora.cod_comercializadora'),
        nullable=False,
        comment='Código de la comercializadora (ENERTOTAL, VATIA, etc.)'
    )
    
    codigo = Column(
        String(30),
        nullable=False,
        comment='Código de la franja (F1, F2, ..., F8)'
    )
    
    tipo_dia = Column(
        String(10),
        nullable=False,
        default='TODOS',
        comment='Tipo de día al que aplica: TODOS, LABORAL, SABADO, DOMINGO, FESTIVO'
    )
    
    activo = Column(
        Boolean,
        nullable=False,
        default=True,
        comment='Indica si la franja está vigente'
    )
    
    # =====================================================
    # CONSTRAINTS
    # =====================================================
    __table_args__ = (
        UniqueConstraint(
            'cod_comercializadora',
            'codigo',
            'tipo_dia',
            name='uq_franja_comercializadora_tipo_dia'
        ),
        CheckConstraint(
            "tipo_dia IN ('TODOS', 'LABORAL', 'SABADO', 'DOMINGO', 'FESTIVO')",
            name='ck_tipo_dia'
        ),
    )
    
    # =====================================================
    # RELACIONES
    # =====================================================
    comercializadora = relationship(
        "Comercializadora",
        backref="franjas_horarias"
    )
    
    configuraciones_franja = relationship(
        "ConfiguracionFranja",
        back_populates="franja_horaria",
        cascade="all, delete-orphan"
    )
    
    configuraciones_hora = relationship(
        "ConfiguracionHora",
        back_populates="franja_horaria"
    )
    
    tarifas_valor = relationship(
        "TarifaValor",
        back_populates="franja"
    )
    
    def __repr__(self) -> str:
        return (
            f"<FranjaHoraria(id={self.id_franja_horaria}, "
            f"codigo='{self.codigo}', "
            f"comercializadora='{self.cod_comercializadora}', "
            f"tipo_dia='{self.tipo_dia}')>"
        )