# app/api/routes/consumption.py

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import Optional, Union
from datetime import date, datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from app.repositories.consumption_repository import ConsumptionRepository
from app.services.consumption_service import ConsumptionService
from app.models.consumption import (
    CurrentConsumptionResponse,
    DailyTotalResponse,
    TimeSeriesResponse
)
from app.models.sync import (
    SyncClienteRequest,
    SyncViviendaRequest,
    SyncMedidorRequest,
    SyncMedidorResponse,
    SyncClienteResponse,
    SyncViviendaResponse,
    SyncEstadoResponse,
    SyncHistorialResponse,
)
from app.services.sync_service import SyncService
from app.services.vivienda_resolver import ViviendaResolverMock
from app.services.tarifa_resolver import TarifaResolverHTTP, TarifaResolverMock
from app.repositories.sync_repository import SyncRepository

from app.config import settings

router = APIRouter(prefix="/api/v1/consumption", tags=["consumption"])


@router.get(
    "/current/{household_id}",
    response_model=CurrentConsumptionResponse,
    summary="Consumo actual",
    description="Obtiene el consumo actual en kW para una vivienda"
)
async def get_current_consumption(
    household_id: str = Path(..., description="ID de la vivienda"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Endpoint para obtener el consumo actual (kW)
    """
    # Convertir ID si es necesario
    if settings.HOUSEHOLD_ID_TYPE == "int":
        try:
            household_id = int(household_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="household_id debe ser un número entero")
    
    repository = ConsumptionRepository(db)
    service = ConsumptionService(repository)
    
    result = await service.get_current_consumption(household_id)
    
    return result


@router.get(
    "/daily-total/{household_id}",
    response_model=DailyTotalResponse,
    summary="Consumo acumulado del día",
    description="Obtiene el consumo total acumulado del día en kWh y su costo"
)
async def get_daily_total(
    household_id: str = Path(..., description="ID de la vivienda"),
    date_param: Optional[date] = Query(None, alias="date", description="Fecha YYYY-MM-DD"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Endpoint para obtener el consumo acumulado del día (kWh) y costo (COP)
    """
    if settings.HOUSEHOLD_ID_TYPE == "int":
        try:
            household_id = int(household_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="household_id debe ser un número entero")
    
    repository = ConsumptionRepository(db)
    service = ConsumptionService(repository)
    
    target_date = date_param or datetime.utcnow().date()
    result = await service.get_daily_total(household_id, target_date)
    
    return result


# ============================================
# NUEVOS ENDPOINTS DE SERIES TEMPORALES
# ============================================

@router.get(
    "/series/hourly/{household_id}",
    response_model=TimeSeriesResponse,
    summary="Serie horaria del día",
    description="Obtiene el consumo por hora para un día específico"
)
async def get_hourly_series(
    household_id: str = Path(..., description="ID de la vivienda"),
    date_param: Optional[date] = Query(None, alias="date", description="Fecha YYYY-MM-DD"),
    start_date_str: Optional[date] = Query(None, alias="date>=", description="Fecha de inicio (YYYY-MM-DD)"),
    end_date_str: Optional[date] = Query(None, alias="date<=", description="Fecha de fin (YYYY-MM-DD)"),
    hours: int = Query(24, ge=1, le=8760, description="Horas hacia atrás (solo si no se envían fechas)"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Obtiene serie temporal con consumo por hora (0-23)
    """
    print(f"Received request for hourly series - household_id: {household_id}, date: {date_param}")
    if settings.HOUSEHOLD_ID_TYPE == "int":
        try:
            household_id = int(household_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="household_id debe ser un número entero")
    
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

        
    
    series = await service.get_hourly_series(household_id, start_date, end_date)
    
    return TimeSeriesResponse(
        id_vivienda=household_id,
        granularity="hour",
        start_date=target_date.isoformat(),
        end_date=target_date.isoformat(),
        labels=[f"{h:02d}:00" for h in range(24)],
        values_kwh=series["consumption_kwh"],
        values_cost=series["costs_cop"]
    )


@router.get(
    "/series/daily/{household_id}",
    response_model=TimeSeriesResponse,
    summary="Serie diaria del mes",
    description="Obtiene el consumo por día para un mes específico"
)
async def get_daily_series(
    household_id: str = Path(..., description="ID de la vivienda"),
    year: int = Query(..., description="Año (ej: 2025)", ge=2020, le=2030),
    month: int = Query(..., description="Mes (1-12)", ge=1, le=12),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Obtiene serie temporal con consumo por día del mes
    """
    if settings.HOUSEHOLD_ID_TYPE == "int":
        try:
            household_id = int(household_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="household_id debe ser un número entero")
    
    repository = ConsumptionRepository(db)
    service = ConsumptionService(repository)
    
    result = await service.get_daily_series(household_id, year, month)
    
    return TimeSeriesResponse(
        id_vivienda=household_id,
        granularity="day",
        start_date=f"{year}-{month:02d}-01",
        end_date=f"{year}-{month:02d}-{result['days_in_month']}",
        labels=result["labels"],
        values_kwh=result["values_kwh"],
        values_cost=result["values_cost"]
    )


@router.get(
    "/series/monthly/{household_id}",
    response_model=TimeSeriesResponse,
    summary="Serie mensual del año",
    description="Obtiene el consumo por mes para un año específico"
)
async def get_monthly_series(
    household_id: str = Path(..., description="ID de la vivienda"),
    year: int = Query(..., description="Año (ej: 2025)", ge=2020, le=2030),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Obtiene serie temporal con consumo por mes del año
    """
    if settings.HOUSEHOLD_ID_TYPE == "int":
        try:
            household_id = int(household_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="household_id debe ser un número entero")
    
    repository = ConsumptionRepository(db)
    service = ConsumptionService(repository)
    
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", 
             "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    
    result = await service.get_monthly_series(household_id, year)
    
    return TimeSeriesResponse(
        id_vivienda=household_id,
        granularity="month",
        start_date=f"{year}-01-01",
        end_date=f"{year}-12-31",
        labels=meses,
        values_kwh=result["values_kwh"],
        values_cost=result["values_cost"]
    )


@router.get(
    "/series/yearly/{household_id}",
    response_model=TimeSeriesResponse,
    summary="Serie anual multi-año",
    description="Obtiene el consumo por año para un rango de años"
)
async def get_yearly_series(
    household_id: str = Path(..., description="ID de la vivienda"),
    start_year: int = Query(..., description="Año inicial", ge=2020, le=2030),
    end_year: int = Query(..., description="Año final", ge=2020, le=2030),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Obtiene serie temporal con consumo por año
    """
    if settings.HOUSEHOLD_ID_TYPE == "int":
        try:
            household_id = int(household_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="household_id debe ser un número entero")
    
    if start_year > end_year:
        raise HTTPException(status_code=400, detail="start_year debe ser menor o igual a end_year")
    
    repository = ConsumptionRepository(db)
    service = ConsumptionService(repository)
    
    result = await service.get_yearly_series(household_id, start_year, end_year)
    
    return TimeSeriesResponse(
        id_vivienda=household_id,
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