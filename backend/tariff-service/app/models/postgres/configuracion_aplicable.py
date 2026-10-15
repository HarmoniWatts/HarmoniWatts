from sqlalchemy import Column, BigInteger, SmallInteger, String, Date, ForeignKey, ForeignKeyConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


# app/models/postgres/configuracion_aplicable.py

class ConfiguracionAplicable(Base):
    __tablename__ = 'configuracion_aplicable'
    
    id_configuracion_aplicable = Column(BigInteger, primary_key=True, autoincrement=True)
    cod_comercializadora = Column(String(20), nullable=False)
    cod_mercado = Column(
        String(30),
        ForeignKey('mercado_red.cod_mercado'),
        nullable=False
    )
    cod_nivel = Column(
        String(15),
        ForeignKey('nivel_tension.cod_nivel'),
        nullable=False
    )
    
    # ⚠️ FK simple (NO compuesta) — solo esta
    id_configuracion_horaria = Column(
        SmallInteger,
        ForeignKey(
            'configuracion_horaria.id_configuracion_horaria',
            name='fk_aplicable_configuracion'
        ),
        nullable=False
    )
    
    vigente_desde = Column(Date, nullable=False)
    vigente_hasta = Column(Date)
    
    __table_args__ = (
        CheckConstraint(
            'vigente_hasta IS NULL OR vigente_hasta >= vigente_desde',
            name='ck_aplicable_fechas'
        ),
    )
    
    # =====================================================
    # RELACIONES
    # =====================================================
    configuracion_horaria = relationship(
        "ConfiguracionHoraria",
        back_populates="configuraciones_aplicables",
        foreign_keys=[id_configuracion_horaria]
    )
    
    mercado_red = relationship(
        "MercadoRed",
        back_populates="configuraciones_aplicables",
        foreign_keys=[cod_mercado]
    )
    
    nivel_tension = relationship(
        "NivelTension",
        back_populates="configuraciones_aplicables",
        foreign_keys=[cod_nivel]
    )