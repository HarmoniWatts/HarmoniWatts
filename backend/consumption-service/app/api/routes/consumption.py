# app/api/routes/consumption.py

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import Optional, Union
from datetime import date, datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from app.repositories.consumption_repository import ConsumptionRepository
from app.services.consumption_service import ConsumptionService
from app.models.consumption import (
    CurrentConsumptionResponse,
    DailyTotalResponse,
    TimeSeriesResponse
)
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
    timezone: str = Query(
        settings.DEFAULT_TIMEZONE,
        alias="timezone",
        description="Zona IANA del día civil (ej. America/Bogota)",
    ),
    db: AsyncIOMotorDatabase = Depends(get_database),
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
    result = await service.get_daily_total(household_id, target_date, timezone)
    
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
    timezone: str = Query(
        settings.DEFAULT_TIMEZONE,
        alias="timezone",
        description="Zona IANA para agrupar horas 0–23 del día civil",
    ),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Obtiene serie temporal con consumo por hora (0-23)
    """
    # print(f"Received request for hourly series - household_id: {household_id}, date: {date_param}")
    if settings.HOUSEHOLD_ID_TYPE == "int":
        try:
            household_id = int(household_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="household_id debe ser un número entero")
    
    repository = ConsumptionRepository(db)
    service = ConsumptionService(repository)
    
    target_date = date_param or datetime.now(timezone.utc).date()
    
    series = await service.get_hourly_series(household_id, target_date, timezone)
    
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
    timezone: str = Query(
        settings.DEFAULT_TIMEZONE,
        alias="timezone",
        description="Zona IANA para asignar cada lectura a un día civil",
    ),
    db: AsyncIOMotorDatabase = Depends(get_database),
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
    
    result = await service.get_daily_series(household_id, year, month, timezone)
    
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
    timezone: str = Query(
        settings.DEFAULT_TIMEZONE,
        alias="timezone",
        description="Zona IANA para agrupar por mes civil",
    ),
    db: AsyncIOMotorDatabase = Depends(get_database),
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
    
    result = await service.get_monthly_series(household_id, year, timezone)
    
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
    timezone: str = Query(
        settings.DEFAULT_TIMEZONE,
        alias="timezone",
        description="Zona IANA (coherente con series mensuales)",
    ),
    db: AsyncIOMotorDatabase = Depends(get_database),
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
    
    result = await service.get_yearly_series(household_id, start_year, end_year, timezone)
    
    return TimeSeriesResponse(
        id_vivienda=household_id,
        granularity="year",
        start_date=f"{start_year}-01-01",
        end_date=f"{end_year}-12-31",
        labels=[str(y) for y in range(start_year, end_year + 1)],
        values_kwh=result["values_kwh"],
        values_cost=result["values_cost"]
    )