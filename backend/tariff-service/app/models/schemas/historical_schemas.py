# app/models/schemas/historical_schemas.py

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# =====================================================
# SCHEMAS BASE (reutilizables)
# =====================================================

class PeriodoRef(BaseModel):
    """Período (año y mes)."""
    anio: int = Field(..., description="Año")
    mes: int = Field(..., ge=1, le=12, description="Mes (1-12)")


class PeriodoVersion(PeriodoRef):
    """Período con la versión publicada que se usó."""
    numero_version: int = Field(..., description="Número de versión de la tarifa publicada")


class Variacion(BaseModel):
    """Variación entre el valor del período A y el del período B."""
    a: Optional[float] = Field(None, description="Valor en el período A")
    b: Optional[float] = Field(None, description="Valor en el período B")
    diferencia: Optional[float] = Field(None, description="b - a")
    porcentaje: Optional[float] = Field(
        None, description="(b - a) / a * 100. None si falta un valor o a es 0"
    )


# =====================================================
# 6. TARIFAS DE UN MES  (GET /tariff/historical/{anio}/{mes})
# =====================================================

class ValorFranjaHistorico(BaseModel):
    """Valor de una franja y las horas que cubre."""
    codigo_franja: str = Field(..., description="Código de la franja (F1..F8)")
    tipo_hora: Optional[str] = Field(None, description="VALLE, MEDIA o PICO")
    valor: float = Field(..., description="Valor en la unidad indicada")
    unidad: str = Field(..., description="Unidad de medida (COP/kWh)")
    horas: List[int] = Field(
        default_factory=list, description="Horas (1-24) que cubre la franja en la configuración del período"
    )


class MonomiaHistorica(BaseModel):
    valor: float = Field(..., description="Valor de la monomia (CU)")
    unidad: str = Field(..., description="Unidad de medida")
    tipo: str = Field("CU", description="Tipo de monomia")


class ComponenteHistorico(BaseModel):
    cod_componente: str = Field(..., description="Código del componente (Gm, Tm, Dm, ...)")
    valor: Optional[float] = Field(None, description="Valor del componente")


class TarifaHistorica(BaseModel):
    """Una tarifa publicada con sus valores y componentes."""
    codigo: str = Field(..., description="Código de la tarifa (MERCADO-NIVEL-TIPO, sin el mes)")
    nombre_tarifa: Optional[str] = None
    cod_comercializadora: str
    cod_mercado: str
    cod_nivel: str
    cod_tipo_tarifa: Optional[str] = None
    resolucion_regulatoria: Optional[str] = None
    numero_version: int = Field(..., description="Versión publicada del período")
    fecha_inicio: date
    fecha_fin: date
    fecha_publicacion: Optional[date] = None
    configuracion_horaria: Optional[str] = Field(None, description="Código de la configuración horaria usada")
    monomia: Optional[MonomiaHistorica] = None
    valores: List[ValorFranjaHistorico] = Field(default_factory=list)
    componentes: List[ComponenteHistorico] = Field(default_factory=list)


class TarifasMesResponse(BaseModel):
    """Respuesta de GET /tariff/historical/{anio}/{mes}."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "anio": 2025,
                "mes": 10,
                "total_tarifas": 1,
                "tarifas": [{
                    "codigo": "CALI-N1_1-A",
                    "nombre_tarifa": "CALI N1_1 tipo A",
                    "cod_comercializadora": "ENERTOTAL",
                    "cod_mercado": "CALI",
                    "cod_nivel": "N1_1",
                    "cod_tipo_tarifa": "A",
                    "resolucion_regulatoria": None,
                    "numero_version": 1,
                    "fecha_inicio": "2025-10-01",
                    "fecha_fin": "2025-10-31",
                    "fecha_publicacion": None,
                    "configuracion_horaria": "CH00",
                    "monomia": {"valor": 888.43, "unidad": "COP/kWh", "tipo": "CU"},
                    "valores": [
                        {"codigo_franja": "F1", "tipo_hora": "VALLE", "valor": 874.09,
                         "unidad": "COP/kWh", "horas": [1, 2, 3, 4, 24]}
                    ],
                    "componentes": [{"cod_componente": "Gm", "valor": 387.07}],
                }],
            }
        }
    )

    anio: int
    mes: int = Field(..., ge=1, le=12)
    total_tarifas: int = Field(..., description="Cantidad de tarifas devueltas")
    tarifas: List[TarifaHistorica] = Field(default_factory=list)


# =====================================================
# 7. TENDENCIAS  (GET /tariff/historical/trends)
# =====================================================

class PuntoTendencia(BaseModel):
    """Un mes de la serie."""
    anio: int
    mes: int = Field(..., ge=1, le=12)
    precio_promedio: Optional[float] = Field(
        None, description="Promedio de las 24 horas del mes (ponderado por horas, no por franjas)"
    )
    precio_min: Optional[float] = Field(None, description="Precio horario mínimo del mes")
    precio_max: Optional[float] = Field(None, description="Precio horario máximo del mes")
    variacion: Optional[float] = Field(
        None, description="% de variación del promedio respecto al mes anterior con datos"
    )
    meses_omitidos: int = Field(
        0, description="Meses sin datos entre este punto y el anterior (0 = meses consecutivos)"
    )
    configuracion: Optional[str] = Field(None, description="Configuración horaria del mes")


class TendenciaResponse(BaseModel):
    """Respuesta de GET /tariff/historical/trends."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cod_comercializadora": "ENERTOTAL",
                "mercado": "META",
                "nivel": "N1_2_1_3",
                "tipo_tarifa": "A",
                "desde": {"anio": 2025, "mes": 1},
                "hasta": {"anio": 2025, "mes": 4},
                "unidad": "COP/kWh",
                "serie": [
                    {"anio": 2025, "mes": 1, "precio_promedio": 766.08, "precio_min": 745.2,
                     "precio_max": 780.1, "variacion": None, "meses_omitidos": 0, "configuracion": "CH00"},
                    {"anio": 2025, "mes": 2, "precio_promedio": 772.45, "precio_min": 750.1,
                     "precio_max": 786.3, "variacion": 0.83, "meses_omitidos": 0, "configuracion": "CH00"},
                    {"anio": 2025, "mes": 4, "precio_promedio": 780.1, "precio_min": 757.0,
                     "precio_max": 795.0, "variacion": 0.99, "meses_omitidos": 1, "configuracion": "CH00"},
                ],
                "meses_faltantes": [{"anio": 2025, "mes": 3}],
                "tendencia_anual": 1.83,
                "precio_min_12m": 745.2,
                "precio_max_12m": 795.0,
                "advertencias": ["Meses sin datos publicados (excluidos de los cálculos): 2025-03."],
            }
        }
    )

    cod_comercializadora: str
    mercado: str
    nivel: str
    tipo_tarifa: str
    desde: PeriodoRef = Field(..., description="Inicio del rango consultado")
    hasta: PeriodoRef = Field(..., description="Fin del rango consultado")
    unidad: str = Field("COP/kWh")
    serie: List[PuntoTendencia] = Field(default_factory=list, description="Solo meses con datos")
    meses_faltantes: List[PeriodoRef] = Field(
        default_factory=list,
        description="Meses del rango sin datos publicados; se excluyen de los cálculos",
    )
    tendencia_anual: Optional[float] = Field(
        None,
        description=(
            "% de variación del promedio entre el primer y el último mes con datos dentro de los "
            "últimos 12 meses de la serie. None si hay menos de 2 meses."
        ),
    )
    precio_min_12m: Optional[float] = Field(None, description="Precio horario mínimo en los últimos 12 meses")
    precio_max_12m: Optional[float] = Field(None, description="Precio horario máximo en los últimos 12 meses")
    advertencias: List[str] = Field(default_factory=list)


# =====================================================
# 8. COMPARACIÓN  (GET /tariff/historical/compare)
# =====================================================

class VariacionHora(Variacion):
    """Variación del precio de una hora. Las franjas pueden diferir si cambió la configuración."""
    hora: int = Field(..., ge=1, le=24, description="Hora (1=00:00-01:00, 24=23:00-24:00)")
    codigo_franja_a: Optional[str] = None
    codigo_franja_b: Optional[str] = None
    tipo_hora_a: Optional[str] = None
    tipo_hora_b: Optional[str] = None


class VariacionTipoHora(Variacion):
    """Variación del precio promedio (ponderado por horas) de un tipo de hora."""
    tipo_hora: str = Field(..., description="VALLE, MEDIA o PICO")
    horas_a: int = Field(..., description="Horas de este tipo en el período A")
    horas_b: int = Field(..., description="Horas de este tipo en el período B")


class VariacionComponente(Variacion):
    cod_componente: str = Field(..., description="Código del componente (Gm, Tm, Dm, ...)")


class CompararResponse(BaseModel):
    """Respuesta de GET /tariff/historical/compare."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cod_comercializadora": "ENERTOTAL",
                "mercado": "CALI",
                "nivel": "N1_1",
                "tipo_tarifa": "A",
                "periodo_a": {"anio": 2025, "mes": 9, "numero_version": 1},
                "periodo_b": {"anio": 2025, "mes": 10, "numero_version": 1},
                "configuracion_a": "CH00",
                "configuracion_b": "CH00",
                "configuracion_distinta": False,
                "unidad": "COP/kWh",
                "precio_promedio_a": 880.12,
                "precio_promedio_b": 888.43,
                "variacion_total": 0.94,
                "variacion_monomia": {"a": 880.0, "b": 888.43, "diferencia": 8.43, "porcentaje": 0.96},
                "variacion_horas": [
                    {"hora": 1, "codigo_franja_a": "F1", "codigo_franja_b": "F1",
                     "tipo_hora_a": "VALLE", "tipo_hora_b": "VALLE",
                     "a": 874.09, "b": 880.5, "diferencia": 6.41, "porcentaje": 0.73}
                ],
                "variacion_tipo_hora": [
                    {"tipo_hora": "VALLE", "horas_a": 5, "horas_b": 5,
                     "a": 874.09, "b": 880.5, "diferencia": 6.41, "porcentaje": 0.73}
                ],
                "variacion_componentes": [
                    {"cod_componente": "Gm", "a": 387.07, "b": 395.1, "diferencia": 8.03, "porcentaje": 2.07}
                ],
                "advertencias": [],
            }
        }
    )

    cod_comercializadora: str
    mercado: str
    nivel: str
    tipo_tarifa: str
    periodo_a: PeriodoVersion
    periodo_b: PeriodoVersion
    configuracion_a: Optional[str] = None
    configuracion_b: Optional[str] = None
    configuracion_distinta: bool = Field(
        ..., description="True si los períodos usan configuraciones horarias distintas"
    )
    unidad: str = Field("COP/kWh")
    precio_promedio_a: Optional[float] = Field(None, description="Promedio de las horas del período A")
    precio_promedio_b: Optional[float] = Field(None, description="Promedio de las horas del período B")
    variacion_total: Optional[float] = Field(
        None, description="% de variación entre precio_promedio_a y precio_promedio_b"
    )
    variacion_monomia: Optional[Variacion] = Field(None, description="Variación de la monomia (si ambos períodos la tienen)")
    variacion_horas: List[VariacionHora] = Field(default_factory=list)
    variacion_tipo_hora: List[VariacionTipoHora] = Field(default_factory=list)
    variacion_componentes: List[VariacionComponente] = Field(default_factory=list)
    advertencias: List[str] = Field(default_factory=list)