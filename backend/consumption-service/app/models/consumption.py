from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class TariffType(str, Enum):
    VALLE = "VALLE"
    MEDIA = "MEDIA"
    PUNTA = "PUNTA"


class ConsumptionRecord(BaseModel):
    """Registro individual de consumo (por hora o minuto)"""
    household_id: str = Field(..., description="ID de la vivienda")
    timestamp: datetime = Field(..., description="Marca de tiempo")
    consumption_kw: float = Field(..., ge=0, description="Potencia activa en kW")
    consumption_kwh: float = Field(..., ge=0, description="Energía en kWh (acumulado del período)")
    tariff_type: Optional[TariffType] = None
    source: str = Field(default="smart_meter", description="Fuente de datos")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class CurrentConsumptionResponse(BaseModel):
    """Respuesta para GET /api/v1/consumption/current/{household_id}"""
    household_id: str
    current_power_kw: float = Field(..., description="Consumo actual en kW")
    last_update: datetime = Field(..., description="Última actualización")
    unit: str = "kW"


class DailyTotalResponse(BaseModel):
    """Respuesta para GET /api/v1/consumption/daily-total/{household_id}"""
    household_id: str
    date: str = Field(..., description="Fecha en formato YYYY-MM-DD")
    total_consumption_kwh: float = Field(..., description="Consumo acumulado del día en kWh")
    average_power_kw: Optional[float] = Field(None, description="Potencia promedio del día")
    peak_power_kw: Optional[float] = Field(None, description="Pico máximo del día")
    unit: str = "kWh"


class ConsumptionDataPoint(BaseModel):
    """Punto de datos para series temporales"""
    timestamp: datetime
    consumption_kw: float
    consumption_kwh: float