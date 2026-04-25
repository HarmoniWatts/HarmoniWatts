# app/models/consumption.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Any
from enum import Enum
from bson import ObjectId


class TarifaAplicada(BaseModel):
    """Estructura de tarifa aplicada al consumo"""
    id_tarifa: int
    id_franja: Optional[int] = None
    nombre_tarifa: Optional[str] = None
    tipo_tarifa: Optional[str] = None
    franja_aplicada: Optional[str] = None
    precio_kwh: float
    costo_total: float
    moneda: str = "COP"


class ContextoTemporal(BaseModel):
    """Contexto temporal del consumo"""
    dia_semana: int
    es_festivo: bool
    hora_del_dia: int
    mes: int
    anio: int
    estacion: Optional[str] = None


class CondicionesExternas(BaseModel):
    """Condiciones climáticas externas"""
    temperatura: Optional[float] = None
    humedad: Optional[float] = None
    precipitacion: Optional[float] = None
    nubosidad: Optional[float] = None
    fuente_clima: str = "No disponible"


class ConsumoEnriquecido(BaseModel):
    """Modelo principal para consumo_enriquecido"""
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    id_vivienda: int = Field(..., description="ID de la vivienda")
    id_tarifa_usuario: Optional[int] = None
    timestamp: datetime = Field(..., description="Marca de tiempo del consumo")
    valor_kwh: float = Field(..., ge=0, description="Consumo en kWh")
    tarifa_aplicada: TarifaAplicada
    tarifas_alternativas: List[Any] = []
    contexto_temporal: ContextoTemporal
    condiciones_externas: CondicionesExternas = CondicionesExternas()
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class ConsumoTimeSeries(BaseModel):
    """Modelo para la colección alterna de time series"""
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    timestamp: datetime
    id_vivienda: int
    tarifa_aplicada: dict
    valor_kwh: float
    fuente: str = "contador"
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# ============================================
# MODELOS DE RESPUESTA PARA API
# ============================================

class CurrentConsumptionResponse(BaseModel):
    """Respuesta para consumo actual"""
    id_vivienda: int
    current_power_kw: float
    last_update: datetime
    unit: str = "kW"


class DailyTotalResponse(BaseModel):
    """Respuesta para consumo acumulado del día"""
    id_vivienda: int
    date: str
    total_consumption_kwh: float
    total_cost_cop: float
    average_power_kw: Optional[float] = None
    peak_power_kw: Optional[float] = None
    peak_hour: Optional[int] = None
    unit_kwh: str = "kWh"


class TimeSeriesResponse(BaseModel):
    """Respuesta genérica para series temporales"""
    id_vivienda: int
    granularity: str  # hour, day, month, year
    start_date: str
    end_date: str
    labels: List[str]
    values_kwh: List[float]
    values_cost: Optional[List[float]] = None
    unit: str = "kWh"


class ConsumptionSummaryResponse(BaseModel):
    """Resumen completo para dashboard"""
    id_vivienda: int
    date: str
    current_power_kw: float
    daily_total_kwh: float
    daily_total_cost_cop: float
    yesterday_variation_percent: Optional[float] = None
    week_average_kwh: Optional[float] = None
    estimated_monthly_kwh: Optional[float] = None