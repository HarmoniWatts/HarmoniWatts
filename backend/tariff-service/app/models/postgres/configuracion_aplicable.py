from sqlalchemy import Column, BigInteger, SmallInteger, String, Date, ForeignKey, ForeignKeyConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class ConfiguracionAplicable(Base):
    """
    Define qué configuración horaria aplica a cada combinación
    de mercado + nivel de tensión, con vigencia temporal.
    """
    __tablename__ = 'configuracion_aplicable'
    
    id_configuracion_aplicable = Column(BigInteger, primary_key=True, autoincrement=True)
    cod_comercializadora = Column(String(20), nullable=False)
    cod_mercado = Column(String(30), ForeignKey('mercado_red.cod_mercado'), nullable=False)
    cod_nivel = Column(String(15), ForeignKey('nivel_tension.cod_nivel'), nullable=False)
    id_configuracion_horaria = Column(SmallInteger, nullable=False)
    vigente_desde = Column(Date, nullable=False)
    vigente_hasta = Column(Date, nullable=True)
    
    __table_args__ = (
        ForeignKeyConstraint(
            ['id_configuracion_horaria', 'cod_comercializadora'],
            ['configuracion_horaria.id_configuracion_horaria',
             'configuracion_horaria.cod_comercializadora'],
            name='fk_aplicable_configuracion'
        ),
        CheckConstraint(
            'vigente_hasta IS NULL OR vigente_hasta >= vigente_desde',
            name='ck_aplicable_fechas'
        ),
    )
    
    # Relaciones
    configuracion_horaria = relationship(
        "ConfiguracionHoraria",
        back_populates="configuraciones_aplicables"
    )
    mercado = relationship("MercadoRed")
    nivel_tension = relationship("NivelTension")