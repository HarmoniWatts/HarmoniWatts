# app/models/postgres/configuracion_hora.py

from sqlalchemy import (
    Column, SmallInteger, ForeignKey,
    PrimaryKeyConstraint, CheckConstraint
)
from app.core.database import Base


class ConfiguracionHora(Base):
    """
    Define la asignación hora → franja dentro de una configuración horaria.
    
    NOTA: Sin relaciones ORM para evitar conflictos con FKs compuestas.
    Las consultas se hacen directamente con joins explícitos.
    """
    __tablename__ = 'configuracion_hora'
    
    id_configuracion_horaria = Column(
        SmallInteger,
        ForeignKey(
            'configuracion_horaria.id_configuracion_horaria',
            name='fk_configuracion_hora_config'
        ),
        primary_key=True,
        nullable=False
    )
    
    hora = Column(
        SmallInteger,
        primary_key=True,
        nullable=False
    )
    
    id_franja_horaria = Column(
        SmallInteger,
        ForeignKey(
            'franja_horaria.id_franja_horaria',
            name='fk_configuracion_hora_franja_simple'
        ),
        nullable=False
    )
    
    __table_args__ = (
        CheckConstraint('hora BETWEEN 1 AND 24', name='ck_hora_rango'),
    )
    
    # ⚠️ SIN RELATIONSHIPS — evitar conflictos con FKs compuestas
    # Se accede a franja_horaria mediante joins explícitos en el repositorio.
    
    def __repr__(self) -> str:
        return (
            f"<ConfiguracionHora(config={self.id_configuracion_horaria}, "
            f"hora={self.hora}, franja={self.id_franja_horaria})>"
        )