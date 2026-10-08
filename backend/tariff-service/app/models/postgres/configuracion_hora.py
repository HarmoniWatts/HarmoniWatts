from sqlalchemy import Column, SmallInteger, ForeignKey, PrimaryKeyConstraint, CheckConstraint, ForeignKeyConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class ConfiguracionHora(Base):
    """
    Define la asignación hora → franja dentro de una configuración horaria.
    
    Cada hora (1-24) se mapea a una única franja horaria.
    
    Nota: hora = 1 es 00:00-01:00; hora = 24 es 23:00-24:00.
    """
    __tablename__ = 'configuracion_hora'
    
    id_configuracion_horaria = Column(
        SmallInteger,
        nullable=False
    )
    
    hora = Column(
        SmallInteger,
        nullable=False,
        comment='Hora del día (1-24). hora=1 es 00:00-01:00; hora=24 es 23:00-24:00'
    )
    
    id_franja_horaria = Column(
        SmallInteger,
        nullable=False
    )
    
    # =====================================================
    # CONSTRAINTS
    # =====================================================
    __table_args__ = (
        PrimaryKeyConstraint('id_configuracion_horaria', 'hora'),
        CheckConstraint(
            'hora BETWEEN 1 AND 24',
            name='ck_hora_rango'
        ),
        ForeignKeyConstraint(
            ['id_configuracion_horaria', 'id_franja_horaria'],
            ['configuracion_franja.id_configuracion_horaria',
             'configuracion_franja.id_franja_horaria'],
            ondelete='CASCADE',
            name='fk_configuracion_hora_franja'
        ),
    )
    
    # =====================================================
    # RELACIONES
    # =====================================================
    configuracion_horaria = relationship(
        "ConfiguracionHoraria",
        back_populates="configuraciones_hora"
    )
    
    franja_horaria = relationship(
        "FranjaHoraria",
        back_populates="configuraciones_hora"
    )
    
    configuracion_franja = relationship(
        "ConfiguracionFranja",
        back_populates="configuraciones_hora",
        primaryjoin=(
            "and_(ConfiguracionHora.id_configuracion_horaria == "
            "ConfiguracionFranja.id_configuracion_horaria, "
            "ConfiguracionHora.id_franja_horaria == "
            "ConfiguracionFranja.id_franja_horaria)"
        ),
        foreign_keys='[ConfiguracionHora.id_configuracion_horaria, '
                     'ConfiguracionHora.id_franja_horaria]',
        viewonly=True
    )
    
    def __repr__(self) -> str:
        return (
            f"<ConfiguracionHora("
            f"config={self.id_configuracion_horaria}, "
            f"hora={self.hora}, "
            f"franja={self.id_franja_horaria})>"
        )