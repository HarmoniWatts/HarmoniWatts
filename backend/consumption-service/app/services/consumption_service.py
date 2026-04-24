# app/services/consumption_service.py

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Union
from app.repositories.consumption_repository import ConsumptionRepository
from app.models.consumption import (
    CurrentConsumptionResponse, 
    DailyTotalResponse,
    TimeSeriesResponse
)
from app.config import settings
import structlog

logger = structlog.get_logger()


class ConsumptionService:
    def __init__(self, repository: ConsumptionRepository):
        self.repository = repository
    
    async def get_current_consumption(
        self, 
        household_id: Union[int, str]
    ) -> CurrentConsumptionResponse:
        """
        Obtiene el consumo actual (última lectura)
        """
        latest = await self.repository.get_latest_reading(household_id)
        
        if not latest:
            logger.warning(
                "no_consumption_data_found",
                household_id=household_id
            )
            return CurrentConsumptionResponse(
                id_vivienda=int(household_id) if isinstance(household_id, str) else household_id,
                current_power_kw=0.0,
                last_update=datetime.utcnow()
            )
        
        return CurrentConsumptionResponse(
            id_vivienda=latest["id_vivienda"],
            current_power_kw=latest["valor_kwh"],
            last_update=latest["timestamp"]
        )
    
    async def get_daily_total(
        self,
        household_id: Union[int, str],
        target_date: Optional[date] = None,
        tz: Optional[str] = None,
    ) -> DailyTotalResponse:
        """
        Obtiene el consumo total acumulado del día con costo
        """
        if target_date is None:
            target_date = datetime.utcnow().date()
        tz = tz or settings.DEFAULT_TIMEZONE

        daily_stats = await self.repository.get_daily_total(household_id, target_date, tz)
        
        if not daily_stats:
            logger.info(
                "no_daily_data_found",
                household_id=household_id,
                date=target_date.isoformat()
            )
            return DailyTotalResponse(
                id_vivienda=int(household_id) if isinstance(household_id, str) else household_id,
                date=target_date.isoformat(),
                total_consumption_kwh=0.0,
                total_cost_cop=0,
                average_power_kw=None,
                peak_power_kw=None,
                peak_hour=None
            )
        
        # Calcular variación vs día anterior
        yesterday_total = await self.repository.get_previous_day_total(household_id, target_date, tz)
        yesterday_variation = None
        if yesterday_total and yesterday_total > 0:
            yesterday_variation = (
                (daily_stats["total_consumption_kwh"] - yesterday_total) / yesterday_total * 100
            )
        
        return DailyTotalResponse(
            id_vivienda=int(household_id) if isinstance(household_id, str) else household_id,
            date=target_date.isoformat(),
            total_consumption_kwh=daily_stats["total_consumption_kwh"],
            total_cost_cop=daily_stats["total_cost_cop"],
            average_power_kw=daily_stats.get("average_power_kw"),
            peak_power_kw=daily_stats.get("peak_power_kw"),
            peak_hour=daily_stats.get("peak_hour")
        )
    
    async def get_hourly_series(
        self, 
        household_id: Union[int, str], 
        target_date: date,
        tz: Optional[str] = None,
    ) -> Dict[str, List[float]]:
        """
        Retorna series horarias de consumo y costo
        """
        tz = tz or settings.DEFAULT_TIMEZONE
        hourly_data = await self.repository.get_hourly_consumption(
            household_id, target_date, tz
        )
        
        consumption = [0.0] * 24
        costs = [0.0] * 24
        
        for item in hourly_data:
            hour = item["hour"]
            consumption[hour] = item["consumption_kwh"]
            costs[hour] = item["total_cost"]
        
        return {
            "consumption_kwh": consumption,
            "costs_cop": costs
        }
    
    async def get_daily_series(
        self, 
        household_id: Union[int, str], 
        year: int, 
        month: int,
        tz: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retorna consumo diario para un mes completo
        """
        from calendar import monthrange
        days_in_month = monthrange(year, month)[1]
        
        start_date = date(year, month, 1)
        end_date = date(year, month, days_in_month)
        tz = tz or settings.DEFAULT_TIMEZONE

        daily_totals = await self.repository.get_daily_totals(
            household_id, start_date, end_date, tz
        )
        
        labels = []
        values_kwh = []
        values_cost = []
        
        for day in range(1, days_in_month + 1):
            current_date = date(year, month, day)
            labels.append(current_date.isoformat())
            
            day_key = current_date.isoformat()
            if day_key in daily_totals:
                values_kwh.append(daily_totals[day_key]["kwh"])
                values_cost.append(daily_totals[day_key]["cost"])
            else:
                values_kwh.append(0.0)
                values_cost.append(0.0)
        
        return {
            "days_in_month": days_in_month,
            "labels": labels,
            "values_kwh": values_kwh,
            "values_cost": values_cost
        }
    
    async def get_monthly_series(
        self, 
        household_id: Union[int, str], 
        year: int,
        tz: Optional[str] = None,
    ) -> Dict[str, List[float]]:
        """
        Retorna consumo mensual para un año
        """
        tz = tz or settings.DEFAULT_TIMEZONE
        monthly_totals = await self.repository.get_monthly_totals(household_id, year, tz)
        
        values_kwh = [0.0] * 12
        values_cost = [0.0] * 12
        
        for month, data in monthly_totals.items():
            values_kwh[month - 1] = data["kwh"]
            values_cost[month - 1] = data["cost"]
        
        return {
            "values_kwh": values_kwh,
            "values_cost": values_cost
        }
    
    async def get_yearly_series(
        self, 
        household_id: Union[int, str], 
        start_year: int, 
        end_year: int,
        tz: Optional[str] = None,
    ) -> Dict[str, List[float]]:
        """
        Retorna consumo anual para un rango de años
        """
        tz = tz or settings.DEFAULT_TIMEZONE
        values_kwh = []
        values_cost = []
        
        for year in range(start_year, end_year + 1):
            monthly_data = await self.repository.get_monthly_totals(household_id, year, tz)
            total_kwh = sum(data["kwh"] for data in monthly_data.values())
            total_cost = sum(data["cost"] for data in monthly_data.values())
            values_kwh.append(total_kwh)
            values_cost.append(total_cost)
        
        return {
            "values_kwh": values_kwh,
            "values_cost": values_cost
        }