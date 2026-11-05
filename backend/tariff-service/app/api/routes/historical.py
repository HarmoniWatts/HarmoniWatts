# app/api/routes/historical.py

import re
from datetime import date
from typing import Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.postgres.tarifa_historica_repository import TarifaHistoricaRepository
from app.services.historical import COMERCIALIZADORA_POR_DEFECTO
from app.services.historical.comparacion_service import (
    ComparacionService,
    PeriodoNoDisponibleError,
)
from app.services.historical.tarifa_historica_service import TarifaHistoricaService
from app.services.historical.tendencia_service import TendenciaService
from app.models.schemas.historical_schemas import (
    CompararResponse,
    TarifasMesResponse,
    TendenciaResponse,
)

router = APIRouter(prefix="/tariff/historical", tags=["Tarifas Históricas"])

_PERIODO_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")


# =====================================================
# Dependencias
# =====================================================
def get_historical_repository(db: Session = Depends(get_db)) -> TarifaHistoricaRepository:
    """Repositorio de consultas históricas (solo lectura)."""
    return TarifaHistoricaRepository(db)


def get_tarifa_historica_service(
    repo: TarifaHistoricaRepository = Depends(get_historical_repository),
) -> TarifaHistoricaService:
    return TarifaHistoricaService(repo=repo)


def get_tendencia_service(
    repo: TarifaHistoricaRepository = Depends(get_historical_repository),
) -> TendenciaService:
    return TendenciaService(repo=repo)


def get_comparacion_service(
    repo: TarifaHistoricaRepository = Depends(get_historical_repository),
) -> ComparacionService:
    return ComparacionService(repo=repo)


def _parse_periodo(valor: str, nombre: str) -> Tuple[int, int]:
    """'2025-10' -> (2025, 10). Responde 422 si el formato no es AAAA-MM."""
    m = _PERIODO_RE.match(valor)
    if not m:
        raise HTTPException(status_code=422, detail=f"{nombre} debe tener el formato AAAA-MM (ej. 2025-10)")
    return int(m.group(1)), int(m.group(2))


# =====================================================
# GET /trends
# (se declara antes de /{anio}/{mes} por claridad)
# =====================================================
@router.get(
    "/trends",
    response_model=TendenciaResponse,
    summary="Tendencia de precios de una tarifa en el tiempo",
)
def get_trends(
    mercado: str = Query(..., description="Código del mercado (ej. META)"),
    nivel: str = Query(..., description="Código del nivel de tensión (ej. N1_2_1_3)"),
    tipo_tarifa: str = Query("A", description="Tipo de tarifa (A, B, C, D)"),
    comercializadora: str = Query(COMERCIALIZADORA_POR_DEFECTO, description="Código de la comercializadora"),
    desde: Optional[date] = Query(None, description="Inicio del rango (se usa el mes). Por defecto, 12 meses antes de 'hasta'"),
    hasta: Optional[date] = Query(None, description="Fin del rango (se usa el mes). Por defecto, el último mes publicado"),
    service: TendenciaService = Depends(get_tendencia_service),
):
    """
    Serie mensual del precio promedio (ponderado por horas) con variación mensual,
    mínimo/máximo de los últimos 12 meses y tendencia anual.

    Los meses sin datos no se usan en los cálculos y se informan en `meses_faltantes`.
    """
    try:
        resultado = service.obtener_tendencia(
            cod_mercado=mercado,
            cod_nivel=nivel,
            cod_tipo_tarifa=tipo_tarifa,
            cod_comercializadora=comercializadora,
            desde=desde,
            hasta=hasta,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if resultado is None:
        raise HTTPException(
            status_code=404,
            detail=f"No hay tarifas publicadas para {mercado} {nivel} tipo {tipo_tarifa} en el rango consultado",
        )
    return resultado


# =====================================================
# GET /compare
# =====================================================
@router.get(
    "/compare",
    response_model=CompararResponse,
    summary="Comparar dos períodos tarifarios",
)
def get_compare(
    mercado: str = Query(..., description="Código del mercado (ej. CALI)"),
    nivel: str = Query(..., description="Código del nivel de tensión (ej. N1_1)"),
    periodo_a: str = Query(..., description="Primer período, formato AAAA-MM"),
    periodo_b: str = Query(..., description="Segundo período, formato AAAA-MM"),
    tipo_tarifa: str = Query("A", description="Tipo de tarifa (A, B, C, D)"),
    comercializadora: str = Query(COMERCIALIZADORA_POR_DEFECTO, description="Código de la comercializadora"),
    service: ComparacionService = Depends(get_comparacion_service),
):
    """
    Variaciones del período B respecto al A, por hora, por tipo de hora (VALLE/MEDIA/PICO)
    y por componente del CU.

    Si la configuración horaria cambió entre los períodos, `configuracion_distinta` es true
    y `advertencias` lo explica (las franjas no son comparables, las horas sí).
    """
    try:
        return service.comparar(
            cod_mercado=mercado,
            cod_nivel=nivel,
            periodo_a=_parse_periodo(periodo_a, "periodo_a"),
            periodo_b=_parse_periodo(periodo_b, "periodo_b"),
            cod_tipo_tarifa=tipo_tarifa,
            cod_comercializadora=comercializadora,
        )
    except PeriodoNoDisponibleError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =====================================================
# GET /{anio}/{mes}
# =====================================================
@router.get(
    "/{anio}/{mes}",
    response_model=TarifasMesResponse,
    summary="Tarifas publicadas de un mes",
)
def get_tarifas_mes(
    anio: int = Path(..., ge=2000, le=2100, description="Año"),
    mes: int = Path(..., ge=1, le=12, description="Mes (1-12)"),
    comercializadora: Optional[str] = Query(None, description="Filtrar por comercializadora"),
    mercado: Optional[str] = Query(None, description="Filtrar por mercado"),
    nivel: Optional[str] = Query(None, description="Filtrar por nivel de tensión"),
    tipo_tarifa: Optional[str] = Query(None, description="Filtrar por tipo de tarifa (A, B, C, D)"),
    service: TarifaHistoricaService = Depends(get_tarifa_historica_service),
):
    """
    Todas las tarifas PUBLICADAS de un mes con sus valores por franja, monomia y componentes.

    Endpoint fino: delega la lógica al TarifaHistoricaService.
    """
    resultado = service.obtener_tarifas_mes(
        anio=anio,
        mes=mes,
        cod_comercializadora=comercializadora,
        cod_mercado=mercado,
        cod_nivel=nivel,
        cod_tipo_tarifa=tipo_tarifa,
    )
    if resultado is None:
        raise HTTPException(
            status_code=404,
            detail=f"No hay tarifas publicadas para {anio}-{mes:02d} con los filtros indicados",
        )
    return resultado