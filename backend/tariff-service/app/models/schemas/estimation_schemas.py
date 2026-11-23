from datetime import date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class EstimacionRequest(BaseModel):
    comercializadora_cod: str = Field(..., description="Código de la comercializadora, ej. ENERTOTAL")
    anio: int = Field(..., ge=2020, le=2100)
    mes: int = Field(..., ge=1, le=12)
    # Opcional: limitar a combinaciones concretas; si es None se estiman todas las activas con histórico
    combinaciones: Optional[List[tuple[str, str, str]]] = None
    # Opcional: sobrescribir la selección de modelos del benchmark
    modelos: Optional[Dict[str, str]] = None
    # Opcional: persistir la estimación como periodo_tarifario BORRADOR + ESTIMADA
    persistir: bool = Field(False, description="Si True, crea periodo_tarifario BORRADOR con observaciones='ESTIMADA...'")


class EstimacionResponse(BaseModel):
    id_estimacion: str
    estado: str                       # pendiente | en_proceso | completado | error
    anio: int
    mes: int
    comercializadora_cod: str
    tarifas_estimadas: int = 0
    tarifas_persistidas: int = 0
    errores: List[str] = Field(default_factory=list)
    mensaje: str = ""


class TarifaEstimadaOut(BaseModel):
    """Forma exacta que devuelve el módulo forecast."""
    mercado: str
    nivel_tension: str
    tipo_tarifa: str
    mes: int
    anio: int
    valores_franja: Dict[str, Optional[float]]
    cu_base: float
    cu_aplicado: float
    componentes_cu: Dict[str, float]
    Cmfj: float


class EstimacionResultadoResponse(BaseModel):
    id_estimacion: str
    estado: str
    anio: int
    mes: int
    tarifas: List[TarifaEstimadaOut] = Field(default_factory=list)
    errores: List[str] = Field(default_factory=list)
    mensaje: str = ""