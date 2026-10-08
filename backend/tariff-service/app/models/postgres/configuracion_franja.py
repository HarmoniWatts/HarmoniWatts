from sqlalchemy import Column, SmallInteger, String, ForeignKey, PrimaryKeyConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class ConfiguracionFranja(Base):
    """
    Define qué franjas existen en cada configuración horaria.
    Las franjas marcadas como N.A. no tienen fila en esta tabla.
    """
    __tablename__ = 'configuracion_franja'
    
    id_configuracion_horaria = Column(
        SmallInteger,
        ForeignKey('configuracion_horaria.id_configuracion_horaria', ondelete='CASCADE'),
        nullable=False
    )
    
    id_franja_horaria = Column(
        SmallInteger,
        ForeignKey('franja_horaria.id_franja_horaria'),
        nullable=False
    )
    
    tipo_hora = Column(
        String(10),
        nullable=True,
        comment='Tipo de hora: PICO, MEDIA, VALLE'
    )
    
    # =====================================================
    # CONSTRAINTS
    # =====================================================
    __table_args__ = (
        PrimaryKeyConstraint('id_configuracion_horaria', 'id_franja_horaria'),
        CheckConstraint(
            "tipo_hora IN ('PICO', 'MEDIA', 'VALLE') OR tipo_hora IS NULL",
            name='ck_tipo_hora'
        ),
    )
    
    # =====================================================
    # RELACIONES
    # =====================================================
    configuracion_horaria = relationship(
        "ConfiguracionHoraria",
        back_populates="configuraciones_franja"
    )
    
    franja_horaria = relationship(
        "FranjaHoraria",
        back_populates="configuraciones_franja"
    )
    
    configuraciones_hora = relationship(
        "ConfiguracionHora",
        back_populates="configuracion_franja"
    )
    
    def __repr__(self) -> str:
        return (
            f"<ConfiguracionFranja("
            f"config={self.id_configuracion_horaria}, "
            f"franja={self.id_franja_horaria})>"
        )