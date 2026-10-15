from sqlalchemy import Column, BigInteger, String, SmallInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class MercadoZona(Base):
    """
    Relación entre municipios (zonas) y mercados-red.
    
    Esta relación es la que valida que un cliente pertenezca a un
    mercado que realmente atienda su zona geográfica.
    """
    __tablename__ = 'mercado_zona'
    
    id_mercado_zona = Column(BigInteger, primary_key=True, autoincrement=True)
    cod_mercado = Column(
        String(30),
        ForeignKey('mercado_red.cod_mercado'),
        nullable=False
    )
    id_zona = Column(
        SmallInteger,
        ForeignKey('zona_geografica.id_zona'),
        nullable=False
    )
    
    __table_args__ = (
        UniqueConstraint('cod_mercado', 'id_zona', name='uq_mercado_zona'),
    )
    
    # Relaciones
    mercado_red = relationship("MercadoRed", back_populates="mercados_zona")
    zona_geografica = relationship("ZonaGeografica", back_populates="mercados_zona")
    
    def __repr__(self) -> str:
        return (
            f"<MercadoZona(cod_mercado='{self.cod_mercado}', "
            f"id_zona={self.id_zona})>"
        )