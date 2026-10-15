from sqlalchemy import Column, String, Boolean, Text, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class TipoTarifa(Base):
    """
    Estructuras o esquemas tarifarios definidos por cada comercializador.
    
    IMPORTANTE:
        A, B, C, D NO son códigos regulatorios universales.
        Cada comercializador define su propia nomenclatura.
    
    Ejemplo para ENERTOTAL:
        A - CU. Aplica para I, C, O, E; estratos 4, 5, 6; y estratos 1, 2, 3
            cuando el consumo es mayor que CS*
        B - CU. Aplica para estrato 3 cuando el consumo es menor que CS*
        C - CU. Aplica para estrato 2 cuando el consumo es menor que CS*
        D - CU. Aplica para estrato 1 cuando el consumo es menor que CS*
    """
    __tablename__ = 'tipo_tarifa'
    
    cod_tipo_tarifa = Column(String(20), nullable=False)
    cod_comercializadora = Column(
        String(20),
        ForeignKey('comercializadora.cod_comercializadora'),
        nullable=False
    )
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    activo = Column(Boolean, nullable=False, default=True)
    
    __table_args__ = (
        PrimaryKeyConstraint('cod_comercializadora', 'cod_tipo_tarifa'),
    )
    
    # Relaciones
    comercializadora = relationship(
        "Comercializadora",
        back_populates="tipos_tarifa"
    )
    tarifas = relationship("Tarifa", back_populates="tipo_tarifa", overlaps="tarifas,comercializadora")
    
    def __repr__(self) -> str:
        return (
            f"<TipoTarifa(cod='{self.cod_tipo_tarifa}', "
            f"comercializadora='{self.cod_comercializadora}')>"
        )