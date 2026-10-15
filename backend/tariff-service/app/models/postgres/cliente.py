from sqlalchemy import (
    Column, BigInteger, SmallInteger, String, Boolean,
    Numeric, TIMESTAMP, ForeignKey, ForeignKeyConstraint,
    CheckConstraint, Index, func
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class Cliente(Base):
    """
    Cliente (suscriptor) del servicio eléctrico.
    
    Reemplaza a la antigua tabla `Usuario` e incorpora:
    - Clasificación del servicio (tipo de cliente + estrato + nivel de tensión)
    - Ubicación geográfica (zona + mercado-red)
    - Comercializadora asignada
    - Consumo de subsistencia (CS) calculado automáticamente por trigger
      según la altura del municipio (173 kWh < 1000 m; 130 kWh >= 1000 m)
    """
    __tablename__ = 'cliente'
    
    # =====================================================
    # IDENTIFICACIÓN
    # =====================================================
    id_cliente = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único del cliente'
    )
    
    # =====================================================
    # CUENTA DE ACCESO
    # =====================================================
    nombre = Column(
        String(100),
        nullable=False,
        comment='Nombre completo del cliente'
    )
    
    email = Column(
        String(100),
        nullable=False,
        unique=True,
        comment='Correo electrónico (usado para login)'
    )
    
    password_hash = Column(
        String(255),
        nullable=False,
        comment='Hash de la contraseña (bcrypt)'
    )
    
    telefono = Column(
        String(20),
        nullable=True,
        comment='Teléfono de contacto'
    )
    
    # =====================================================
    # CLASIFICACIÓN DEL SERVICIO
    # =====================================================
    cod_tipo_cliente = Column(
        String(1),
        ForeignKey('tipo_cliente.cod_tipo_cliente'),
        nullable=False,
        comment='Tipo de cliente: I, C, O, E, R (Industrial, Comercial, Oficial, Especial, Residencial)'
    )
    
    estrato = Column(
        SmallInteger,
        nullable=True,
        comment='Estrato socioeconómico 1-6 (solo para cliente residenciales tipo R)'
    )
    
    cod_nivel = Column(
        String(15),
        ForeignKey('nivel_tension.cod_nivel'),
        nullable=False,
        comment='Nivel de tensión de conexión (N1_1, N1_2, N2, N3, N4, etc.)'
    )
    
    # =====================================================
    # UBICACIÓN Y PROVEEDOR
    # =====================================================
    id_zona = Column(
        SmallInteger,
        ForeignKey('zona_geografica.id_zona'),    # ← FK simple para trigger CS
        nullable=False
    )
    cod_mercado = Column(
        String(30),
        ForeignKey('mercado_red.cod_mercado'),    # ← FK simple para relación
        nullable=False
    )
    cod_comercializadora = Column(
        String(20),
        ForeignKey('comercializadora.cod_comercializadora'),
        nullable=False
    )
    
    # =====================================================
    # CONSUMO DE SUBSISTENCIA (calculado por trigger)
    # =====================================================
    cs_kwh_mes = Column(
        Numeric(8, 2),
        nullable=True,
        comment='Consumo de subsistencia: 173 kWh (< 1000 m) o 130 kWh (>= 1000 m)'
    )
    
    # =====================================================
    # AUDITORÍA
    # =====================================================
    fecha_registro = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment='Fecha de alta del cliente'
    )
    
    ultimo_acceso = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment='Fecha del último inicio de sesión'
    )
    
    activo = Column(
        Boolean,
        nullable=False,
        default=True,
        comment='Indica si la cuenta está activa'
    )
    
    # =====================================================
    # CONSTRAINTS
    # =====================================================
    __table_args__ = (
        # FK compuesta a mercado_zona (el mercado debe atender la zona)
        ForeignKeyConstraint(
            ['cod_mercado', 'id_zona'],
            ['mercado_zona.cod_mercado', 'mercado_zona.id_zona'],
            name='fk_cliente_mercado_zona'
        ),
        
        # FK simple a zona_geografica (necesaria para el trigger de CS)
        ForeignKeyConstraint(
            ['id_zona'],
            ['zona_geografica.id_zona'],
            name='fk_cliente_zona'
        ),
        
        # Estrato entre 1 y 6
        CheckConstraint(
            'estrato BETWEEN 1 AND 6',
            name='ck_cliente_estrato'
        ),
        
        # Estrato obligatorio solo para residenciales
        CheckConstraint(
            "(cod_tipo_cliente = 'R') = (estrato IS NOT NULL)",
            name='ck_cliente_estrato_residencial'
        ),
        
        # Índices
        Index('idx_cliente_mercado_zona', 'cod_mercado', 'id_zona'),
        Index('idx_cliente_tarifa', 'cod_comercializadora', 'cod_mercado', 'cod_nivel'),
        Index('idx_cliente_email', 'email'),
        Index('idx_cliente_activo', 'activo'),
    )
    
    # =====================================================
    # RELACIONES
    # =====================================================
    
    # Clasificación
    tipo_cliente = relationship(
        "TipoCliente",
        back_populates="clientes"
    )
    
    nivel_tension = relationship(
        "NivelTension",
        back_populates="clientes"
    )
    
    # Ubicación
    zona_geografica = relationship(
        "ZonaGeografica",
        foreign_keys=[id_zona],
        backref="cliente"
    )
    
    mercado_red = relationship(
        "MercadoRed",
        foreign_keys=[cod_mercado],
        backref="cliente"
    )
    
    # Comercializadora
    comercializadora = relationship(
        "Comercializadora",
        back_populates="clientes"
    )
    
    # Relaciones 1:N con otras tablas
    # viviendas = relationship(
    #     "Vivienda",
    #     back_populates="cliente",
    #     cascade="all, delete-orphan"
    # )
    
    # conexiones_externas = relationship(
    #     "ConexionExterna",
    #     back_populates="cliente",
    #     cascade="all, delete-orphan"
    # )
    
    # tarifas_usuario = relationship(
    #     "TarifaUsuario",
    #     back_populates="cliente",
    #     cascade="all, delete-orphan"
    # )
    
    def __repr__(self) -> str:
        return (
            f"<Cliente("
            f"id={self.id_cliente}, "
            f"nombre='{self.nombre}', "
            f"email='{self.email}', "
            f"tipo='{self.cod_tipo_cliente}', "
            f"estrato={self.estrato}, "
            f"nivel='{self.cod_nivel}')>"
        )
    
    # =====================================================
    # PROPIEDADES CALCULADAS
    # =====================================================
    
    @property
    def es_residencial(self) -> bool:
        """Indica si el cliente es residencial"""
        return self.cod_tipo_cliente == 'R'
    
    @property
    def es_subsidiado(self) -> bool:
        """
        Indica si el cliente puede aplicar a subsidios
        (residencial en estratos 1, 2 o 3)
        """
        return self.es_residencial and self.estrato in (1, 2, 3)
    
    @property
    def codigo_tarifa_esperado(self) -> str:
        """
        Genera el código de tarifa esperado según la clasificación.
        Útil para buscar la tarifa activa en el repositorio.
        """
        partes = [
            self.cod_mercado,
            self.cod_nivel,
            self.cod_tipo_cliente
        ]
        if self.es_residencial and self.estrato:
            partes.append(f"E{self.estrato}")
        return "-".join(partes)