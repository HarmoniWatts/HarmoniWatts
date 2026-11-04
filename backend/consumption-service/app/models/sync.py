from pydantic import BaseModel, Field, ConfigDict
from datetime import date, datetime
from typing import Optional, List


# =====================================================
# SCHEMAS DE REQUEST
# =====================================================
class SyncViviendaRequest(BaseModel):
    """Request para sincronización manual por vivienda."""
    fecha_inicio: date = Field(..., description="Fecha inicial (YYYY-MM-DD)")
    fecha_fin: date = Field(..., description="Fecha final (YYYY-MM-DD)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "fecha_inicio": "2026-07-01",
                "fecha_fin": "2026-07-20",
            }
        }
    )

class SyncClienteRequest(BaseModel):
    """Request para sincronización manual por cliente."""
    fecha_inicio: date = Field(..., description="Fecha inicial (YYYY-MM-DD)")
    fecha_fin: date = Field(..., description="Fecha final (YYYY-MM-DD)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "fecha_inicio": "2026-07-01",
                "fecha_fin": "2026-07-20",
            }
        }
    )

class SyncMedidorRequest(BaseModel):
    """Request para sincronización manual."""
    meter_no: str = Field(..., description="Número de medidor")
    fecha_inicio: date = Field(..., description="Fecha inicial (YYYY-MM-DD)")
    fecha_fin: date = Field(..., description="Fecha final (YYYY-MM-DD)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "meter_no": "MNFFF016E250",
                "fecha_inicio": "2026-07-01",
                "fecha_fin": "2026-07-20",
            }
        }
    )
   
    
class SyncManualRequest(BaseModel):
    """Request para sincronización manual."""
    meter_no: str = Field(..., description="Número de medidor")
    fecha_inicio: date = Field(..., description="Fecha inicial (YYYY-MM-DD)")
    fecha_fin: date = Field(..., description="Fecha final (YYYY-MM-DD)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "meter_no": "MNFFF016E250",
                "fecha_inicio": "2026-07-01",
                "fecha_fin": "2026-07-20",
            }
        }
    )


class SyncAutomaticaRequest(BaseModel):
    """Request para sincronización automática (últimas N horas)."""
    meter_no: Optional[str] = Field(None, description="Si no se especifica, sincroniza todos")
    horas_atras: int = Field(24, ge=1, le=720, description="Horas hacia atrás")


# =====================================================
# SCHEMAS DE RESPONSE
# =====================================================

class SyncViviendaResponse(BaseModel):
    """Respuesta al disparar una sincronización."""
    id_sincronizacion: str = Field(..., description="ID único de la sincronización")
    estado: str = Field(..., description="pendiente, en_proceso, completado, error")
    id_vivienda: Optional[int] = None
    medidores: Optional[List] = None
    total_medidores: Optional[int] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    mensaje: str
    detalles: List
    
class SyncClienteResponse(BaseModel):
    """Respuesta al disparar una sincronización."""
    id_sincronizacion: str = Field(..., description="ID único de la sincronización")
    estado: str = Field(..., description="pendiente, en_proceso, completado, error")
    id_cliente: Optional[int] = None
    medidores: Optional[List] = None
    total_medidores: Optional[int] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    mensaje: str
    detalles: dict
    
class SyncMedidorResponse(BaseModel):
    """Respuesta al disparar una sincronización."""
    id_sincronizacion: str = Field(..., description="ID único de la sincronización")
    estado: str = Field(..., description="pendiente, en_proceso, completado, error")
    meter_no: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    mensaje: str

class SyncInitResponse(BaseModel):
    """Respuesta al disparar una sincronización."""
    id_sincronizacion: str = Field(..., description="ID único de la sincronización")
    estado: str = Field(..., description="pendiente, en_proceso, completado, error")
    meter_no: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    mensaje: str


class SyncEstadoResponse(BaseModel):
    """Estado de una sincronización."""
    id_sincronizacion: str
    estado: str
    meter_no: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    registros_obtenidos: int = 0
    registros_insertados: int = 0
    registros_duplicados: int = 0
    errores: List[str] = Field(default_factory=list)
    duracion_seg: Optional[int] = None
    creada_en: Optional[datetime] = None
    finalizada_en: Optional[datetime] = None


class SyncHistorialItem(BaseModel):
    """Ítem del historial de sincronizaciones."""
    id_sincronizacion: str
    meter_no: Optional[str] = None
    estado: str
    registros_insertados: int
    fecha_sincronizacion: datetime


class SyncHistorialResponse(BaseModel):
    """Historial de sincronizaciones."""
    total: int
    limit: int
    offset: int
    items: List[SyncHistorialItem]