from fastapi import Query
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List, Optional

from app.config import settings


class PrediccionHora(BaseModel):
    timestamp: str
    consumo_estimado_kwh: float
    intervalo_confianza_inf: Optional[float] = None
    intervalo_confianza_sup: Optional[float] = None


class ModeloInfo(BaseModel):
    nombre: str
    version: str


class PrediccionResponse(BaseModel):
    no_contrat: str
    cod_comercializadora: str
    id_cliente: Optional[int]
    meter_no: str
    generado_en: str
    horizonte_horas: int
    modelo: ModeloInfo
    predicciones: List[PrediccionHora]
    metadatos: dict
    id_prediccion: Optional[str] = None
    
class ContratoPrediccionRequest(BaseModel):
    """Request para predicción por número de contrato."""
    id_cliente: Optional[int] = Field(
        None, description="ID del cliente (opcional: sin él no se resuelve la tarifa de cada lectura)"
    )
    horizonte: int = Query(settings.HORIZONTE_HORAS, ge=24, le=168),
    persistir: bool = Query(True),
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id_cliente": 12345,
                "horizonte": 168,
                "persistir": True,
            }
        }
    )


class BatchPrediccionRequest(BaseModel):
    meters: List[str] = Field(..., min_length=1, max_length=100)
    horizonte: int = Field(168, ge=24, le=168)
    persistir: bool = True


class BatchPrediccionResponse(BaseModel):
    total_medidores: int
    exitosos: int
    fallidos: int
    omitidos: List[dict]
    resultados: List[dict]


class ModelStatusResponse(BaseModel):
    nombre: str
    version: str
    uri: str
    cargado: bool
    horizonte_horas: int
    min_history_horas: int


# ---------------------------------------------------------------- HAR-25
class PuntoHistorico(BaseModel):
    timestamp: str
    real_kwh: float
    estimado_kwh: float


class PuntoFuturo(BaseModel):
    timestamp: str
    estimado_kwh: float
    inferior_kwh: float
    superior_kwh: float


class Confianza(BaseModel):
    nivel: str  # alto | medio | bajo
    error_diario_pct: Optional[float] = None
    error_horario_pct: Optional[float] = None
    dias_evaluados: int
    horas_evaluadas: int
    metodo: str


class PronosticoResponse(BaseModel):
    no_contrato: str
    cod_comercializadora: str
    meter_no: str
    generado_en: str
    ultima_lectura: str
    modelo: ModeloInfo
    historico: List[PuntoHistorico]
    futuro: List[PuntoFuturo]
    confianza: Confianza
    metadatos: dict
