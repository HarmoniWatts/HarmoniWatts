from sqlalchemy import Column, BigInteger, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class ComponenteValorMes(Base):
    __tablename__ = 'componente_valor_mes'
    
    id_componente_valor_mes = Column(BigInteger, primary_key=True)
    id_periodo_tarifario = Column(BigInteger, ForeignKey('periodo_tarifario.id_periodo_tarifario'), nullable=False)
    cod_componente = Column(String(15), ForeignKey('componente_costo.cod_componente'), nullable=False)
    valor = Column(Numeric(12, 4), nullable=False)
    
    # Relaciones
    periodo = relationship("PeriodoTarifario", back_populates="componentes")
    componente = relationship("ComponenteCosto")