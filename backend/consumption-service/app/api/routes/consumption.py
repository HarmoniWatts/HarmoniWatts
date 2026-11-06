# app/api/routes/consumption.py

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import Optional
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from app.core.local_calendar import utc_range_for_local_calendar_day
from app.repositories.consumption_repository import ConsumptionRepository
from app.services.consumption_service import ConsumptionService
from app.models.consumption import (
    CurrentConsumptionResponse,
    DailyTotalResponse,
    TimeSeriesResponse
)
from app.models.sync import (
    SyncClienteRequest,
    SyncContratoRequest,
    SyncViviendaRequest,
    SyncMedidorRequest,
    SyncMedidorResponse,
    SyncClienteResponse,
    SyncViviendaResponse,
    SyncContratoResponse,
    SyncEstadoResponse,
    SyncHistorialResponse,
)
from app.services.sync_service import SyncService
from app.services.vivienda_resolver import ViviendaResolverMock
from app.services.tarifa_resolver import TarifaResolverHTTP, TarifaResolverMock
from app.repositories.sync_repository import SyncRepository

from app.config import settings

import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/consumption", tags=["consumption"])



def _normalizar_contrato(no_contrat: str, cod_retail: str) -> tuple[str, str]:
    """Los consumos se identifican por (no_contrato, cod_comercializadora), ambos texto."""
    no_contrat = (no_contrat or "").strip()
    cod_retail = (cod_retail or "").strip().upper()
    if not no_contrat or not cod_retail:
        raise HTTPException(
            status_code=400,
            detail="Se requieren el número de contrato y el código de la comercializadora",
        )
    return no_contrat, cod_retail


@router.get(
    "/current/{no_contrat}/{cod_retail}",
    response_model=CurrentConsumptionResponse,
    summary="Consumo actual",
    description="Obtiene el consumo actual en kW para una vivienda"
)
async def get_current_consumption(
    no_contrat: str = Path(..., description="No de la cuenta"),
    cod_retail: str = Path(..., description="Código de la comercializadora"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Endpoint para obtener el consumo actual (kW)
    """
    no_contrat, cod_retail = _normalizar_contrato(no_contrat, cod_retail)
    
    repository = ConsumptionRepository(db)
    service = ConsumptionService(repository)
    
    result = await service.get_current_consumption(no_contrat, cod_retail)
    
    return result


@router.get(
    "/daily-total/{no_contrat}/{cod_retail}",
    response_model=DailyTotalResponse,
    summary="Consumo acumulado del día",
    description="Obtiene el consumo total acumulado del día en kWh y su costo"
)
async def get_daily_total(
    no_contrat: str = Path(..., description="No de la cuenta"),
    cod_retail: str = Path(..., description="Código de la comercializadora"),
    date_param: Optional[date] = Query(None, alias="date", description="Fecha YYYY-MM-DD"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Endpoint para obtener el consumo acumulado del día (kWh) y costo (COP)
    """
    no_contrat, cod_retail = _normalizar_contrato(no_contrat, cod_retail)
    
    repository = ConsumptionRepository(db)
    service = ConsumptionService(repository)
    
    target_date = date_param or datetime.utcnow().date()
    result = await service.get_daily_total(no_contrat, cod_retail, target_date)
    
    return result


# ============================================
# NUEVOS ENDPOINTS DE SERIES TEMPORALES
# ============================================

@router.get(
    "/series/hourly-days/{no_contrat}/{cod_retail}",
    response_model=TimeSeriesResponse,
    summary="Serie horaria de varios días",
    description="Obtiene el consumo por hora para un rango de días (hasta 7 días) en formato de serie temporal"
)
async def get_hourly_days_series(
    no_contrat: str = Path(..., description="No de la cuenta"),
    cod_retail: str = Path(..., description="Código de la comercializadora"),
    start_date_str: Optional[date] = Query(None, alias="date>", description="Fecha de inicio (YYYY-MM-DD)"),
    end_date_str: Optional[date] = Query(None, alias="date<", description="Fecha de fin (YYYY-MM-DD)"),
    hours: int = Query(24, ge=1, le=8760, description="Horas hacia atrás (solo si no se envían fechas)"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Obtiene serie temporal con consumo por hora (0-23)
    """
    # print(f"Received request for hourly series - no_contrat: {no_contrat}")
    no_contrat, cod_retail = _normalizar_contrato(no_contrat, cod_retail)
    
    repository = ConsumptionRepository(db)
    service = ConsumptionService(repository)
    
    
    local_tz = ZoneInfo("America/Bogota")
    
    target_date = datetime.now(local_tz).date()
    start_date = datetime.combine(target_date, datetime.min.time())
    end_date = datetime.combine(target_date, datetime.max.time())
    
    # 1. Determinar el inicio y fin del rango
    print(f"start_date_str: {start_date_str}, end_date_str: {end_date_str}")
    if start_date_str and end_date_str:
        start_date = datetime.combine(start_date_str, datetime.min.time(), tzinfo=local_tz)
        print(f"start_date_str: {start_date_str}, start_date: {start_date}")
        end_date = datetime.combine(end_date_str, datetime.max.time(), tzinfo=local_tz)
        print(f"end_date_str: {end_date_str}, end_date: {end_date}")
    elif hours:
        end_date = datetime.now(local_tz)
        start_date = end_date - timedelta(hours=hours)

        
    
    series = await service.get_hourly_days_series(no_contrat, cod_retail, start_date, end_date)
    
    logger.info(f"Hourly days series - {series}")
    
    return TimeSeriesResponse(
        no_contrat=no_contrat,
        cod_comercializadora=cod_retail,
        granularity="hour",
        start_date=target_date.isoformat(),
        end_date=target_date.isoformat(),
        labels=[f"{h:02d}:00" for h in range(24)],
        values_kwh=series["consumption_kwh"],
        values_cost=series["costs_cop"]
    )
    
@router.get(
    "/series/hourly/{no_contrat}/{cod_retail}",
    response_model=TimeSeriesResponse,
    summary="Serie horaria de varios días",
    description="Obtiene el consumo por hora para un rango de días (hasta 7 días) en formato de serie temporal"
)
async def get_hourly_series(
    no_contrat: str = Path(..., description="No de la cuenta"),
    cod_retail: str = Path(..., description="Código de la comercializadora"),
    date_param: Optional[date] = Query(None, alias="date", description="Fecha YYYY-MM-DD"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Obtiene serie temporal con consumo por hora (0-23)
    """
    # print(f"Received request for hourly series - no_contrat: {no_contrat}")
    no_contrat, cod_retail = _normalizar_contrato(no_contrat, cod_retail)
    
    repository = ConsumptionRepository(db)
    service = ConsumptionService(repository)
    
    
    local_tz = ZoneInfo("America/Bogota")
    
    target_date = date_param or datetime.now(local_tz).date()
    
    start_date, end_date = utc_range_for_local_calendar_day(target_date, local_tz)

        
    
    series = await service.get_hourly_series(no_contrat, cod_retail, start_date, end_date)
    
    return TimeSeriesResponse(
        no_contrat=no_contrat,
        cod_comercializadora=cod_retail,
        granularity="hour",
        start_date=target_date.isoformat(),
        end_date=target_date.isoformat(),
        labels=[f"{h:02d}:00" for h in range(24)],
        values_kwh=series["consumption_kwh"],
        values_cost=series["costs_cop"]
    )
    
@router.get(
    "/series/raws/{no_contrat}/{cod_retail}",
    response_model=TimeSeriesResponse,
    summary="Serie horaria de varios días",
    description="Obtiene el consumo por hora para un rango de días (hasta 7 días) en formato de serie temporal"
)
async def get_raw_series(
    no_contrat: str = Path(..., description="No de la cuenta"),
    cod_retail: str = Path(..., description="Código de la comercializadora"),
    date_param: Optional[date] = Query(None, alias="date", description="Fecha YYYY-MM-DD"),
    start_date_str: Optional[date] = Query(None, alias="date>", description="Fecha de inicio (YYYY-MM-DD)"),
    end_date_str: Optional[date] = Query(None, alias="date<", description="Fecha de fin (YYYY-MM-DD)"),
    hours: int = Query(24, ge=1, le=8760, description="Horas hacia atrás (solo si no se envían fechas)"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Obtiene serie temporal con consumo por hora (0-23)
    """
    print(f"Received request for hourly series - no_contrat: {no_contrat}, date: {date_param}")
    no_contrat, cod_retail = _normalizar_contrato(no_contrat, cod_retail)
    
    repository = ConsumptionRepository(db)
    service = ConsumptionService(repository)
    
    
    local_tz = ZoneInfo("America/Bogota")
    
    target_date = date_param or datetime.now(local_tz).date()
    start_date = datetime.combine(target_date, datetime.min.time())
    end_date = datetime.combine(target_date, datetime.max.time())
    
    # 1. Determinar el inicio y fin del rango
    if start_date_str and end_date_str:
        start_date = datetime.combine(start_date_str, datetime.min.time(), tzinfo=local_tz)
        end_date = datetime.combine(end_date_str, datetime.max.time(), tzinfo=local_tz)
    elif hours:
        end_date = datetime.now(local_tz)
        start_date = end_date - timedelta(hours=hours)

        
    
    series = await service.get_hourly_series(no_contrat, cod_retail, start_date, end_date)
    
    return TimeSeriesResponse(
        no_contrat=no_contrat,
        cod_comercializadora=cod_retail,
        granularity="hour",
        start_date=target_date.isoformat(),
        end_date=target_date.isoformat(),
        labels=[f"{h:02d}:00" for h in range(24)],
        values_kwh=series["consumption_kwh"],
        values_cost=series["costs_cop"]
    )


@router.get(
    "/series/daily/{no_contrat}/{cod_retail}",
    response_model=TimeSeriesResponse,
    summary="Serie diaria del mes",
    description="Obtiene el consumo por día para un mes específico"
)
async def get_daily_series(
    no_contrat: str = Path(..., description="No de la cuenta"),
    cod_retail: str = Path(..., description="Código de la comercializadora"),
    year: int = Query(..., description="Año (ej: 2025)", ge=2020, le=2030),
    month: int = Query(..., description="Mes (1-12)", ge=1, le=12),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Obtiene serie temporal con consumo por día del mes
    """
    no_contrat, cod_retail = _normalizar_contrato(no_contrat, cod_retail)
    
    repository = ConsumptionRepository(db)
    service = ConsumptionService(repository)
    
    result = await service.get_daily_series(no_contrat, cod_retail, year, month)
    
    return TimeSeriesResponse(
        no_contrat=no_contrat,
        cod_comercializadora=cod_retail,
        granularity="day",
        start_date=f"{year}-{month:02d}-01",
        end_date=f"{year}-{month:02d}-{result['days_in_month']}",
        labels=result["labels"],
        values_kwh=result["values_kwh"],
        values_cost=result["values_cost"]
    )


@router.get(
    "/series/monthly/{no_contrat}/{cod_retail}",
    response_model=TimeSeriesResponse,
    summary="Serie mensual del año",
    description="Obtiene el consumo por mes para un año específico"
)
async def get_monthly_series(
    no_contrat: str = Path(..., description="No de la cuenta"),
    cod_retail: str = Path(..., description="Código de la comercializadora"),
    year: int = Query(..., description="Año (ej: 2025)", ge=2020, le=2030),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Obtiene serie temporal con consumo por mes del año
    """
    no_contrat, cod_retail = _normalizar_contrato(no_contrat, cod_retail)
    
    repository = ConsumptionRepository(db)
    service = ConsumptionService(repository)
    
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", 
             "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    
    result = await service.get_monthly_series(no_contrat, cod_retail, year)
    
    return TimeSeriesResponse(
        no_contrat=no_contrat,
        cod_comercializadora=cod_retail,
        granularity="month",
        start_date=f"{year}-01-01",
        end_date=f"{year}-12-31",
        labels=meses,
        values_kwh=result["values_kwh"],
        values_cost=result["values_cost"]
    )


@router.get(
    "/series/yearly/{no_contrat}/{cod_retail}",
    response_model=TimeSeriesResponse,
    summary="Serie anual multi-año",
    description="Obtiene el consumo por año para un rango de años"
)
async def get_yearly_series(
    no_contrat: str = Path(..., description="No de la cuenta"),
    cod_retail: str = Path(..., description="Código de la comercializadora"),
    start_year: int = Query(..., description="Año inicial", ge=2020, le=2030),
    end_year: int = Query(..., description="Año final", ge=2020, le=2030),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Obtiene serie temporal con consumo por año
    """
    no_contrat, cod_retail = _normalizar_contrato(no_contrat, cod_retail)
    
    if start_year > end_year:
        raise HTTPException(status_code=400, detail="start_year debe ser menor o igual a end_year")
    
    repository = ConsumptionRepository(db)
    service = ConsumptionService(repository)
    
    result = await service.get_yearly_series(no_contrat, cod_retail, start_year, end_year)
    
    return TimeSeriesResponse(
        no_contrat=no_contrat,
        cod_comercializadora=cod_retail,
        granularity="year",
        start_date=f"{start_year}-01-01",
        end_date=f"{end_year}-12-31",
        labels=[str(y) for y in range(start_year, end_year + 1)],
        values_kwh=result["values_kwh"],
        values_cost=result["values_cost"]
    )
    
    
# =====================================================
# DEPENDENCIAS
# =====================================================

def get_sync_service() -> SyncService:
    """
    Construye SyncService con implementaciones por defecto.
    
    - ViviendaResolver: MOCK (hasta tener user-service)
    - TarifaResolver: HTTP (tariff-service) con fallback a MOCK
    """
    vivienda_resolver = ViviendaResolverMock()
    
    # Elegir tarifa resolver según entorno
    if settings.ENVIRONMENT == "development" and not settings.TARIFF_SERVICE_URL:
        tarifa_resolver = TarifaResolverMock()
    else:
        tarifa_resolver = TarifaResolverHTTP(
            base_url=settings.TARIFF_SERVICE_URL,
        )
    
    return SyncService(
        vivienda_resolver=vivienda_resolver,
        tarifa_resolver=tarifa_resolver,
    )


def get_sync_repository() -> SyncRepository:
    return SyncRepository()


# =====================================================
# ENDPOINTS
# =====================================================


# =====================================================
# SINCRONIZACIÓN MANUAL
# =====================================================


@router.post("/sync/manual/contrato/{no_contrato}/{cod_retail}", response_model=SyncContratoResponse, status_code=200)
async def sync_por_contrato(
    no_contrato: str,
    cod_retail: str,
    request: SyncContratoRequest,
    service: SyncService = Depends(get_sync_service),
):
    """
    Dispara una sincronización manual para un medidor asociado a un contrato en un rango de fechas.
    
    La sincronización se ejecuta en segundo plano (background task).
    Consulta el estado en /consumption/sync/estado/{id}.
    """
    # Ejecutar en background (o Celery si está configurado)
    resultado = await service.sincronizar_contrato(
        no_contrato=no_contrato,
        cod_retail=cod_retail,
        id_cliente=request.id_cliente,
        fecha_inicio=request.fecha_inicio,
        fecha_fin=request.fecha_fin,
    )
   
    return SyncContratoResponse(
        id_sincronizacion=resultado["id_sincronizacion"],
        estado=resultado["estado"],
        no_contrato=resultado["no_contrato"],
        cod_comercializadora=resultado["cod_comercializadora"],
        id_cliente=resultado["id_cliente"],
        id_vivienda=resultado["id_vivienda"],
        serie_medidor=resultado["serie_medidor"],
        fecha_inicio=request.fecha_inicio,
        fecha_fin=request.fecha_fin
    )


@router.post("/sync/manual/vivienda/{id_vivienda}", response_model=SyncViviendaResponse, status_code=202)
async def sync_por_vivienda(
    id_vivienda: int,
    request: SyncViviendaRequest,
    service: SyncService = Depends(get_sync_service),
):
    """
    Dispara una sincronización manual para un medidor en un rango de fechas.
    
    La sincronización se ejecuta en segundo plano (background task).
    Consulta el estado en /consumption/sync/estado/{id}.
    """
    # Ejecutar en background (o Celery si está configurado)
    resultado = await service.sincronizar_vivienda(
        id_vivienda=id_vivienda,
        fecha_inicio=request.fecha_inicio,
        fecha_fin=request.fecha_fin,
    )
   
    return SyncViviendaResponse(
        id_sincronizacion=resultado["id_sincronizacion"],
        estado=resultado["estado"],
        id_vivienda=resultado["id_vivienda"],
        medidores=resultado["medidores"],
        total_medidores=resultado["total_medidores"],
        fecha_inicio=request.fecha_inicio,
        fecha_fin=request.fecha_fin,
        mensaje=resultado["mensaje"],
        detalles = resultado["detalles"],
    )

@router.post("/sync/manual/cliente/{id_cliente}", response_model=SyncClienteResponse, status_code=202)
async def sync_por_cliente(
    id_cliente: int,
    request: SyncClienteRequest,
    service: SyncService = Depends(get_sync_service),
):
    """
    Dispara una sincronización manual para un medidor en un rango de fechas.
    
    La sincronización se ejecuta en segundo plano (background task).
    Consulta el estado en /consumption/sync/estado/{id}.
    """
    # Ejecutar en background (o Celery si está configurado)
    resultado = await service.sincronizar_vivienda(
        id_cliente=request.id_cliente,
        fecha_inicio=request.fecha_inicio,
        fecha_fin=request.fecha_fin,
    )
    return SyncClienteResponse(
        id_sincronizacion=resultado["id_sincronizacion"],
        estado=resultado["estado"],
        id_cliente=resultado.get("id_cliente"),
        medidores=resultado.get("medidores"),
        total_medidores=resultado.get("total_medidores"),
        fecha_inicio=request.fecha_inicio,
        fecha_fin=request.fecha_fin,
        mensaje=resultado["mensaje"],
        detalles = resultado["detalles"],
    )

@router.post("/sync/manual/medidor/{meter_no}", response_model=SyncMedidorResponse, status_code=202)
async def sync_manual(
    request: SyncMedidorRequest,
    service: SyncService = Depends(get_sync_service),
):
    """
    Dispara una sincronización manual para un medidor en un rango de fechas.
    
    La sincronización se ejecuta en segundo plano (background task).
    Consulta el estado en /consumption/sync/estado/{id}.
    """
    # Ejecutar en background (o Celery si está configurado)
    resultado = await service.sincronizar_medidor(
        meter_no=request.meter_no,
        fecha_inicio=request.fecha_inicio,
        fecha_fin=request.fecha_fin,
    )
    return SyncMedidorResponse(
        id_sincronizacion=resultado["id_sincronizacion"],
        estado=resultado["estado"],
        meter_no=resultado.get("meter_no"),
        fecha_inicio=request.fecha_inicio,
        fecha_fin=request.fecha_fin,
        mensaje="Sincronización completada",
    )


# =====================================================
# CONSULTAR ESTADO
# =====================================================

@router.get("/sync/estado/{id_sincronizacion}", response_model=SyncEstadoResponse)
async def get_sync_estado(
    id_sincronizacion: str,
    repo: SyncRepository = Depends(get_sync_repository),
):
    """Consulta el estado de una sincronización."""
    doc = await repo.obtener_sync_estado(id_sincronizacion)
    
    if not doc:
        raise HTTPException(404, f"Sincronización no encontrada: {id_sincronizacion}")
    
    # return SyncEstadoResponse(
    #     id_sincronizacion=doc["id_sincronizacion"],
    #     estado=doc["estado"],
    #     meter_no=doc.get("meter_no"),
    #     registros_obtenidos=doc.get("registros_obtenidos", 0),
    #     registros_insertados=doc.get("registros_insertados", 0),
    #     registros_duplicados=doc.get("registros_duplicados", 0),
    #     errores=doc.get("errores", []),
    #     duracion_seg=doc.get("duracion_seg"),
    #     creada_en=doc.get("creada_en"),
    #     finalizada_en=doc.get("finalizada_en"),
    # )
    return SyncEstadoResponse(**doc)


# =====================================================
# HISTORIAL
# =====================================================

@router.get("/sync/historial", response_model=SyncHistorialResponse)
async def get_sync_historial(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    repo: SyncRepository = Depends(get_sync_repository),
):
    """Consulta el historial de sincronizaciones."""
    return await repo.obtener_historial(limit=limit, offset=offset)