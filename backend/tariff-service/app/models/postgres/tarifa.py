from sqlalchemy import Column, BigInteger, ForeignKeyConstraint, String, Boolean, TIMESTAMP, func, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Tarifa(Base):
    __tablename__ = 'tarifa'
    
    id_tarifa = Column(BigInteger, primary_key=True)
    cod_comercializadora = Column(String(20),ForeignKey('comercializadora.cod_comercializadora'),nullable=False)
    cod_mercado = Column(String(30), ForeignKey('mercado_red.cod_mercado'), nullable=False)
    cod_nivel = Column(String(15), ForeignKey('nivel_tension.cod_nivel'), nullable=False)
    cod_tipo_tarifa = Column(String(20))
    codigo_tarifa = Column(String(50), unique=True)
    nombre_tarifa = Column(String(200))
    estrato = Column(String(5))
    resolucion_regulatoria = Column(String(100))
    activa = Column(Boolean, default=True)
    fecha_registro = Column(TIMESTAMP, server_default=func.now())
    
    # Relaciones
    __table_args__ = (
        ForeignKeyConstraint(
            ['cod_comercializadora'],
            ['comercializadora.cod_comercializadora'],
            name='fk_tarifa_comercializadora'
        ),
        ForeignKeyConstraint(
            ['cod_mercado'],
            ['mercado_red.cod_mercado'],
            name='fk_tarifa_mercado'
        ),
        ForeignKeyConstraint(
            ['cod_nivel'],
            ['nivel_tension.cod_nivel'],
            name='fk_tarifa_nivel_tension'
        ),
        ForeignKeyConstraint(
            ['cod_comercializadora', 'cod_tipo_tarifa'],
            ['tipo_tarifa.cod_comercializadora', 'tipo_tarifa.cod_tipo_tarifa'],
            name='fk_tarifa_tipo_tarifa'
        ),
    )
    
    # Relaciones
    comercializadora = relationship("Comercializadora", back_populates="tarifas",overlaps="tarifas")
    tipo_tarifa = relationship(
        "TipoTarifa",
        back_populates="tarifas",
        overlaps="comercializadora,tarifas"   # ← Silencia el warning
    )
    periodos = relationship(
        "PeriodoTarifario",
        back_populates="tarifa",
        overlaps="comercializadora,tarifas",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Tarifa(id={self.id_tarifa}, codigo='{self.codigo_tarifa}')>"