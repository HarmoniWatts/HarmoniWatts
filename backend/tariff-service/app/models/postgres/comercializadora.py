from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base


class Comercializadora(Base):
    """
    Empresa que provee el servicio eléctrico.
    
    Esta entidad representa al comercializador que:
    - Define sus propias franjas horarias (F1..F8)
    - Define sus propias configuraciones horarias (CH00..CH09)
    - Define sus propios tipos de tarifa (A, B, C, D, ...)
    - Publica tarifas mensuales con sus valores por franja y componentes
    """
    __tablename__ = 'comercializadora'
    
    # =====================================================
    # CAMPOS
    # =====================================================
    cod_comercializadora = Column(
        String(20),
        primary_key=True,
        comment='Código mnemotécnico/sigla de la comercializadora (ENERTOTAL, VATIA, QIENERGY, etc.)'
    )
    
    nombre = Column(
        String(100),
        nullable=False,
        unique=True,
        comment='Nombre completo de la comercializadora'
    )
    
    nit = Column(
        String(20),
        unique=True,
        nullable=True,
        comment='NIT de la comercializadora'
    )
    
    sitio_web = Column(
        String(255),
        nullable=True,
        comment='URL del sitio web oficial'
    )
    
    activo = Column(
        Boolean,
        nullable=False,
        default=True,
        comment='Indica si la comercializadora está vigente'
    )
    
    # =====================================================
    # RELACIONES
    # =====================================================
    
    # Franjas horarias (F1..F8) definidas por esta comercializadora
    franjas_horarias = relationship(
        "FranjaHoraria",
        back_populates="comercializadora",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # Configuraciones horarias (CH00..CH09) definidas por esta comercializadora
    configuraciones_horarias = relationship(
        "ConfiguracionHoraria",
        back_populates="comercializadora",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # Tipos de tarifa (A, B, C, D, ...) definidos por esta comercializadora
    tipos_tarifa = relationship(
        "TipoTarifa",
        back_populates="comercializadora",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # Clientes atendidos por esta comercializadora
    clientes = relationship(
        "Cliente",
        back_populates="comercializadora",
        lazy="selectin"
    )
    
    # Tarifas publicadas por esta comercializadora
    tarifas = relationship(
        "Tarifa",
        back_populates="comercializadora",
        lazy="selectin"
    )
    
    # =====================================================
    # REPRESENTACIÓN
    # =====================================================
    def __repr__(self) -> str:
        return (
            f"<Comercializadora("
            f"codigo='{self.cod_comercializadora}', "
            f"nombre='{self.nombre}', "
            f"activo={self.activo})>"
        )