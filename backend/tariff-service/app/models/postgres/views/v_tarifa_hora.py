# app/models/postgres/views/v_tarifa_hora.py

from sqlalchemy import (
    Column, BigInteger, SmallInteger, String, Numeric, Date, Integer
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class VTarifaHora(Base):
    """
    Vista que combina tarifa_valor + periodo_tarifario + tarifa +
    configuracion_horaria + configuracion_hora + franja_horaria +
    configuracion_franja.
    
    Permite consultar directamente el precio por hora (1..24) de cada
    tarifa y período sin hacer joins manuales.
    
    Es una VISTA — no permite INSERT/UPDATE/DELETE.
    """
    __tablename__ = 'v_tarifa_hora'
    __table_args__ = {
        'info': {'is_view': True}
    }
    
    # =====================================================
    # PK COMPUESTA ARTIFICIAL
    # =====================================================
    # La vista no tiene PK natural, pero SQLAlchemy requiere una.
    # Usamos la combinación (id_periodo_tarifario, hora) porque
    # es única por tarifa/período.
    id_periodo_tarifario = Column(
        BigInteger,
        primary_key=True,
        comment='ID del período tarifario'
    )
    
    hora = Column(
        SmallInteger,
        primary_key=True,
        comment='Hora del día (1=00:00-01:00, 24=23:00-24:00)'
    )
    
    # =====================================================
    # DATOS DE TARIFA
    # =====================================================
    id_tarifa = Column(
        BigInteger,
        nullable=False,
        comment='ID de la tarifa'
    )
    
    codigo_tarifa = Column(
        String(50),
        comment='Código único de la tarifa'
    )
    
    cod_comercializadora = Column(
        String(20),
        comment='Código de la comercializadora'
    )
    
    cod_mercado = Column(
        String(30),
        comment='Código del mercado'
    )
    
    cod_nivel = Column(
        String(15),
        comment='Código del nivel de tensión'
    )
    
    cod_tipo_tarifa = Column(
        String(20),
        comment='Código del tipo de tarifa (A, B, C, D)'
    )
    
    # =====================================================
    # DATOS DEL PERÍODO
    # =====================================================
    anio = Column(
        SmallInteger,
        nullable=False,
        comment='Año del período'
    )
    
    mes = Column(
        SmallInteger,
        nullable=False,
        comment='Mes del período (1-12)'
    )
    
    fecha_inicio = Column(
        Date,
        comment='Fecha de inicio de vigencia'
    )
    
    fecha_fin = Column(
        Date,
        comment='Fecha de fin de vigencia'
    )
    
    numero_version = Column(
        Integer,
        comment='Número de versión del período'
    )
    
    estado = Column(
        String(20),
        comment='Estado: BORRADOR, PUBLICADA, SUPERADA, ANULADA'
    )
    
    # =====================================================
    # DATOS DE CONFIGURACIÓN HORARIA
    # =====================================================
    id_configuracion_horaria = Column(
        SmallInteger,
        comment='ID de la configuración horaria'
    )
    
    configuracion = Column(
        String(30),
        comment='Código de la configuración horaria (CH00, CH01, ...)'
    )
    
    # =====================================================
    # DATOS DE FRANJA
    # =====================================================
    id_franja_horaria = Column(
        SmallInteger,
        comment='ID de la franja horaria'
    )
    
    franja = Column(
        String(30),
        comment='Código de la franja (F1, F2, ..., F8)'
    )
    
    tipo_dia = Column(
        String(10),
        comment='Tipo de día: TODOS, LABORAL, SABADO, DOMINGO, FESTIVO'
    )
    
    tipo_hora = Column(
        String(10),
        comment='Tipo de hora: PICO, MEDIA, VALLE'
    )
    
    # =====================================================
    # DATOS DE VALOR
    # =====================================================
    valor = Column(
        Numeric(18, 6),
        nullable=False,
        comment='Valor del precio para esa hora'
    )
    
    unidad = Column(
        String(30),
        nullable=False,
        default='COP/kWh',
        comment='Unidad de medida'
    )
    
    # =====================================================
    # RELACIONES (opcionales)
    # =====================================================
    # Puedes agregar relaciones a las tablas subyacentes si lo necesitas.
    # Como es una vista, las relaciones son de solo lectura.
    
    # Ejemplo: relación con PeriodoTarifario
    # periodo = relationship(
    #     "PeriodoTarifario",
    #     primaryjoin="VTarifaHora.id_periodo_tarifario == PeriodoTarifario.id_periodo_tarifario",
    #     foreign_keys="VTarifaHora.id_periodo_tarifario",
    #     viewonly=True,
    # )
    
    # =====================================================
    # REPRESENTACIÓN
    # =====================================================
    def __repr__(self) -> str:
        return (
            f"<VTarifaHora(tarifa='{self.codigo_tarifa}', "
            f"periodo={self.anio}-{self.mes}, "
            f"hora={self.hora}, "
            f"franja='{self.franja}', "
            f"valor={self.valor})>"
        )