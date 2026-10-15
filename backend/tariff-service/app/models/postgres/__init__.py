"""
Modelos SQLAlchemy para PostgreSQL.
Importar TODOS los modelos aquí para que Base.metadata los reconozca
y las relaciones por nombre se resuelvan correctamente.
"""

# 1. Catálogos base (sin dependencias externas)
from app.models.postgres.comercializadora import Comercializadora
from app.models.postgres.tipo_cliente import TipoCliente
from app.models.postgres.nivel_tension import NivelTension
from app.models.postgres.operador_red import OperadorRed
from app.models.postgres.tipo_cargo import TipoCargo
from app.models.postgres.componente_costo import ComponenteCosto

# 2. Catálogos dependientes
from app.models.postgres.zona_geografica import ZonaGeografica
from app.models.postgres.mercado_red import MercadoRed
from app.models.postgres.mercado_zona import MercadoZona
from app.models.postgres.tipo_tarifa import TipoTarifa

# 3. Entidades principales
from app.models.postgres.cliente import Cliente
from app.models.postgres.tarifa import Tarifa

# 4. Franjas y configuraciones horarias
from app.models.postgres.franja_horaria import FranjaHoraria
from app.models.postgres.configuracion_horaria import ConfiguracionHoraria
from app.models.postgres.configuracion_franja import ConfiguracionFranja
from app.models.postgres.configuracion_hora import ConfiguracionHora
from app.models.postgres.configuracion_aplicable import ConfiguracionAplicable

# 5. Períodos y valores
from app.models.postgres.periodo_tarifario import PeriodoTarifario
from app.models.postgres.tarifa_valor import TarifaValor
from app.models.postgres.componente_valor_mes import ComponenteValorMes

# 6. Vistas
from app.models.postgres.views.v_tarifa_hora import VTarifaHora

__all__ = [
    # Catálogos base
    "Comercializadora",
    "TipoCliente",
    "NivelTension",
    "OperadorRed",
    "TipoCargo",
    "ComponenteCosto",
    # Catálogos dependientes
    "ZonaGeografica",
    "MercadoRed",
    "MercadoZona",
    "TipoTarifa",
    # Entidades principales
    "Cliente",
    "Tarifa",
    # Franjas y configuraciones
    "FranjaHoraria",
    "ConfiguracionHoraria",
    "ConfiguracionFranja",
    "ConfiguracionHora",
    "ConfiguracionAplicable",
    # Períodos y valores
    "PeriodoTarifario",
    "TarifaValor",
    "ComponenteValorMes",
    #vistas
    "VTarifaHora",
]