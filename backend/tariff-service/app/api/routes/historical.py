# app/api/routes/historical.py

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.repositories.postgres.cliente_repository import ClienteRepository
from app.repositories.postgres.tarifa_repository import TarifaRepository

from app.services.business.tarifa_selector import TarifaSelector

from app.services.historical.tarifa_historica_service import TarifaHistoricaService

from app.models.schemas.historical_schemas import (
    HistoricoPeriodoResponse,
    TendenciaTarifaResponse,
    ComparacionTarifaResponse,
)

from app.api.dependencies import (
    get_tarifa_repository,
    get_tarifa_selector,
    get_cliente_repository,
    # get_current_cliente
)

router = APIRouter(
    prefix="/tariff/historical",
    tags=["Tarifas Históricas"]
)


# =====================================================
# Dependencias
# =====================================================

def get_tarifa_historica_service(
    repo: TarifaRepository = Depends(get_tarifa_repository),
    cliente_repo: ClienteRepository = Depends(get_cliente_repository),
    selector: TarifaSelector = Depends(get_tarifa_selector),
) -> TarifaHistoricaService:
    """
    Provee el servicio de tarifas históricas.
    """
    return TarifaHistoricaService(
        repo=repo,
        cliente_repo=cliente_repo,
        selector=selector,
    )


# =====================================================
# GET /period/{id_cliente}/{anio}/{mes}
# =====================================================

@router.get(
    "/period/{id_cliente}/{anio}/{mes}",
    response_model=HistoricoPeriodoResponse,
    summary="Tarifas históricas de un período"
)
def get_historical_period(
    id_cliente: int,
    anio: int,
    mes: int,
    consumo_mensual_kwh: Optional[float] = Query(
        None,
        description="Consumo mensual del cliente"
    ),
    service: TarifaHistoricaService = Depends(
        get_tarifa_historica_service
    ),
    # cliente_autenticado=Depends(get_current_cliente),
):
    """
    Obtiene las tarifas aplicadas durante un mes específico.
    """

    # if cliente_autenticado.id_cliente != id_cliente:
    #     raise HTTPException(
    #         status_code=403,
    #         detail="No autorizado"
    #     )

    resultado = service.obtener_historico_periodo(
        id_cliente=id_cliente,
        anio=anio,
        mes=mes,
        consumo_mensual_kwh=consumo_mensual_kwh
    )

    if resultado is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No existe información histórica "
                f"para {mes}/{anio}"
            )
        )

    return resultado


# =====================================================
# GET /trends/{id_cliente}
# =====================================================

@router.get(
    "/trends/{id_cliente}",
    response_model=TendenciaTarifaResponse,
    summary="Análisis de tendencias tarifarias"
)
def get_tariff_trends(
    id_cliente: int,
    fecha_inicio: date = Query(
        ...,
        description="Fecha inicial"
    ),
    fecha_fin: date = Query(
        ...,
        description="Fecha final"
    ),
    consumo_mensual_kwh: Optional[float] = Query(
        None,
        description="Consumo mensual del cliente"
    ),
    service: TarifaHistoricaService = Depends(
        get_tarifa_historica_service
    ),
    # cliente_autenticado=Depends(get_current_cliente),
):
    """
    Devuelve métricas estadísticas y evolución de precios.
    """

    resultado = service.obtener_tendencias(
        id_cliente=id_cliente,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        consumo_mensual_kwh=consumo_mensual_kwh
    )

    if resultado is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "No se encontraron datos para "
                "calcular tendencias"
            )
        )

    return resultado


# =====================================================
# GET /compare/{id_cliente}
# =====================================================

@router.get(
    "/compare/{id_cliente}",
    response_model=ComparacionTarifaResponse,
    summary="Comparación de períodos tarifarios"
)
def compare_periods(
    id_cliente: int,

    fecha_inicio_1: date = Query(
        ...,
        description="Fecha inicial del período 1"
    ),
    fecha_fin_1: date = Query(
        ...,
        description="Fecha final del período 1"
    ),

    fecha_inicio_2: date = Query(
        ...,
        description="Fecha inicial del período 2"
    ),
    fecha_fin_2: date = Query(
        ...,
        description="Fecha final del período 2"
    ),

    consumo_mensual_kwh: Optional[float] = Query(
        None,
        description="Consumo mensual del cliente"
    ),

    service: TarifaHistoricaService = Depends(
        get_tarifa_historica_service
    ),
    # cliente_autenticado=Depends(get_current_cliente),
):
    """
    Compara dos períodos tarifarios diferentes.
    """

    resultado = service.comparar_periodos(
        id_cliente=id_cliente,

        fecha_inicio_1=fecha_inicio_1,
        fecha_fin_1=fecha_fin_1,

        fecha_inicio_2=fecha_inicio_2,
        fecha_fin_2=fecha_fin_2,

        consumo_mensual_kwh=consumo_mensual_kwh
    )

    if resultado is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "No fue posible realizar "
                "la comparación de períodos"
            )
        )

    return resultado


# =====================================================
# GET /export/{id_cliente}
# =====================================================

@router.get(
    "/export/{id_cliente}",
    summary="Exportar histórico tarifario"
)
def export_historical_data(
    id_cliente: int,

    fecha_inicio: date = Query(...),
    fecha_fin: date = Query(...),

    formato: str = Query(
        "csv",
        pattern="^(csv|xlsx|json)$"
    ),

    consumo_mensual_kwh: Optional[float] = Query(
        None,
        description="Consumo mensual del cliente"
    ),

    service: TarifaHistoricaService = Depends(
        get_tarifa_historica_service
    ),
    # cliente_autenticado=Depends(get_current_cliente),
):
    """
    Exporta información tarifaria histórica.
    """

    resultado = service.exportar_historico(
        id_cliente=id_cliente,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        formato=formato,
        consumo_mensual_kwh=consumo_mensual_kwh
    )

    if resultado is None:
        raise HTTPException(
            status_code=404,
            detail="No existen datos para exportar"
        )

    return resultado