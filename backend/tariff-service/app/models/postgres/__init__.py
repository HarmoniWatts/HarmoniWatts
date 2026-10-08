"""
Modelos SQLAlchemy para PostgreSQL.
Importar todos los modelos aquí para que Base.metadata los reconozca.
"""

#from app.models.postgres.comercializadora import Comercializadora
from app.models.postgres.franja_horaria import FranjaHoraria
from app.models.postgres.configuracion_horaria import ConfiguracionHoraria
from app.models.postgres.configuracion_franja import ConfiguracionFranja
from app.models.postgres.configuracion_hora import ConfiguracionHora
from app.models.postgres.configuracion_aplicable import ConfiguracionAplicable
from app.models.postgres.tarifa import Tarifa
from app.models.postgres.periodo_tarifario import PeriodoTarifario
from app.models.postgres.tarifa_valor import TarifaValor
from app.models.postgres.componente_valor_mes import ComponenteValorMes

__all__ = [
    "Comercializadora",
    "FranjaHoraria",
    "ConfiguracionHoraria",
    "ConfiguracionFranja",
    "ConfiguracionHora",
    "ConfiguracionAplicable",
    "Tarifa",
    "PeriodoTarifario",
    "TarifaValor",
    "ComponenteValorMes",
]