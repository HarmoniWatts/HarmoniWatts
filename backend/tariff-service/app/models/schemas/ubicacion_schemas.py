from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.schemas.active_schemas import (
    ComponenteCU,
    MonomiaInfo,
    PeriodoInfo,
    PrecioHora,
    TarifaInfo,
)


class CiudadTarifaria(BaseModel):
    """Municipio + mercado de comercialización (fila de mercado_zona)."""
    id_zona: int
    cod_mercado: str
    municipio: str
    departamento: Optional[str] = None
    altura: Optional[int] = None
    nombre_mercado: str
    operador_red: Optional[str] = None


class SeleccionTarifa(BaseModel):
    """Cómo se eligió la tarifa a partir de la ubicación y el estrato."""
    estrato: int
    cs_kwh_mes: int = Field(..., description="Consumo de subsistencia según la altura del municipio")
    cod_tipo_tarifa_solicitado: str = Field(..., description="Tipo según CREG 119/2007 (A, B, C, D)")
    cod_tipo_tarifa_aplicado: str = Field(..., description="Tipo con tarifa publicada que se usó")
    cod_nivel: str
    nota: Optional[str] = Field(None, description="Presente si se usó una tarifa alternativa")


class TarifaUbicacionResponse(BaseModel):
    """Tarifa vigente de una vivienda (ubicación + estrato) para una fecha."""
    fecha: date
    ciudad: CiudadTarifaria
    seleccion: SeleccionTarifa
    tarifa: TarifaInfo
    periodo: PeriodoInfo
    monomia: Optional[MonomiaInfo] = None
    precios: List[PrecioHora] = Field(default_factory=list, description="24 precios (hora 1..24)")
    componentes: List[ComponenteCU] = Field(default_factory=list)


class MesCalendario(BaseModel):
    mes: int = Field(..., ge=1, le=12)
    publicado: bool
    numero_version: Optional[int] = None
    versiones: int = 0
    fecha_publicacion: Optional[date] = None
    precio_min: Optional[float] = None
    precio_max: Optional[float] = None
    precio_promedio: Optional[float] = None
    monomia: Optional[float] = None
    unidad: str = "COP/kWh"


class CalendarioTarifasResponse(BaseModel):
    anio: int
    ciudad: CiudadTarifaria
    seleccion: SeleccionTarifa
    codigo_tarifa: str
    meses: List[MesCalendario]
