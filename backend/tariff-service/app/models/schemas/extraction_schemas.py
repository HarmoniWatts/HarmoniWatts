from pydantic import BaseModel, Field, model_validator
from datetime import date
from typing import Optional, List, Self
from enum import Enum

class ModoExtraccion(str, Enum):
    MANUAL = "manual"
    AUTOMATICA = "automatica"

class FrecuenciaAutomatica(str, Enum):
    SEMANAL = "semanal"
    MENSUAL = "mensual"

class ExtraccionManualRequest(BaseModel):
    """Request para extracción manual de tarifas"""
    comercializadora_id: int = Field(..., description="ID de la comercializadora")
    fecha_inicio: date = Field(..., description="Fecha de inicio del rango")
    fecha_fin: date = Field(..., description="Fecha de fin del rango")
    urls_pdf: Optional[List[str]] = Field(None, description="URLs específicas de PDFs (opcional)")
    
    @model_validator(mode='after')
    def validar_fechas(self) -> Self:
        # En Pydantic V2, los valores ya están validados y se accede a ellos con self
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError('fecha_fin debe ser >= fecha_inicio')
        return self

class ExtraccionAutomaticaRequest(BaseModel):
    """Request para configurar extracción automática"""
    comercializadora_id: int
    frecuencia: FrecuenciaAutomatica
    activa: bool = True

class TarifaExtraida(BaseModel):
    """Tarifa extraída del PDF"""
    codigo_tarifa: str
    nombre_tarifa: str
    mercado: str
    nivel_tension: str
    tipo_tarifa: Optional[str] = None
    fecha_inicio: date
    fecha_fin: date
    resolucion_regulatoria: Optional[str] = None
    
    # Franjas horarias
    franjas: List['FranjaExtraida'] = []
    
    # Componentes
    componentes: List['ComponenteExtraido'] = []

class FranjaExtraida(BaseModel):
    codigo_franja: str  # F1-F8
    valor: float
    definicion_horas: str
    orden: int

class ComponenteExtraido(BaseModel):
    codigo_componente: str  # G, T, D, CV, PR, R
    nombre_componente: str
    valor: float
    unidad: str = "$/kWh"

class ExtraccionResponse(BaseModel):
    """Respuesta de extracción"""
    id_extraccion: str
    estado: str  # 'pendiente', 'en_proceso', 'completado', 'error'
    modo: ModoExtraccion
    tarifas_extraidas: int = 0
    tarifas_insertadas: int = 0
    errores: List[str] = []
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    mensaje: str