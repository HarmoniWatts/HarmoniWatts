# app/models/postgres/configuracion_franja.py

from sqlalchemy import (
    Column, SmallInteger, String,
    ForeignKey, PrimaryKeyConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class ConfiguracionFranja(Base):
    """
    Define qué franjas existen en cada configuración horaria.
    Las franjas marcadas como N.A. no tienen fila en esta tabla.
    
    NOTA: Sin relación a ConfiguracionHora para evitar conflictos
    con FKs compuestas. Se accede mediante joins explícitos.
    """
    __tablename__ = 'configuracion_franja'
    
    id_configuracion_horaria = Column(
        SmallInteger,
        ForeignKey(
            'configuracion_horaria.id_configuracion_horaria',
            name='fk_configuracion_franja_config',
            ondelete='CASCADE'
        ),
        primary_key=True,
        nullable=False
    )
    
    id_franja_horaria = Column(
        SmallInteger,
        ForeignKey(
            'franja_horaria.id_franja_horaria',
            name='fk_configuracion_franja_franja'
        ),
        primary_key=True,
        nullable=False
    )
    
    tipo_hora = Column(
        String(10),
        nullable=True,
        comment='Tipo de hora: PICO, MEDIA, VALLE'
    )
    
    __table_args__ = (
        CheckConstraint(
            "tipo_hora IN ('PICO', 'MEDIA', 'VALLE') OR tipo_hora IS NULL",
            name='ck_tipo_hora'
        ),
    )
    
    # =====================================================
    # RELACIONES — solo las que NO tienen conflicto
    # =====================================================
    configuracion_horaria = relationship(
        "ConfiguracionHoraria",
        back_populates="configuraciones_franja",
        foreign_keys=[id_configuracion_horaria]
    )
    
    franja_horaria = relationship(
        "FranjaHoraria",
        back_populates="configuraciones_franja",
        foreign_keys=[id_franja_horaria]
    )
    
    # ⚠️ ELIMINADA — conflicto con FK compuesta:
    # configuraciones_hora = relationship("ConfiguracionHora", ...)
    
    def __repr__(self) -> str:
        return (
            f"<ConfiguracionFranja(config={self.id_configuracion_horaria}, "
            f"franja={self.id_franja_horaria})>"
        )