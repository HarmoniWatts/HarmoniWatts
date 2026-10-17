# app/api/routes/ubicacion.py
"""
Tarifas por ubicación de la vivienda (municipio + mercado) y estrato.

Lo consume el frontend (módulo de tarifas y dashboard) con los datos que el
usuario configura en "Mi vivienda". No recibe datos personales: solo la
ciudad, el mercado y el estrato.
"""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_tarifa_repository, get_tarifa_selector
from app.core.database import get_db
from app.models.schemas.ubicacion_schemas import (
    CalendarioTarifasResponse,
    CiudadTarifaria,
    TarifaUbicacionResponse,
)
from app.repositories.postgres.tarifa_repository import TarifaRepository
from app.services.active.ubicacion_service import UbicacionNoEncontrada, UbicacionTarifaService
from app.services.business.tarifa_selector import TarifaSelector

router = APIRouter(prefix="/tariff/ubicacion", tags=["Tarifas por ubicación"])


def get_ubicacion_service(
    db: Session = Depends(get_db),
    repo: TarifaRepository = Depends(get_tarifa_repository),
    selector: TarifaSelector = Depends(get_tarifa_selector),
) -> UbicacionTarifaService:
    return UbicacionTarifaService(db=db, repo=repo, selector=selector)


@router.get(
    "/ciudades",
    response_model=List[CiudadTarifaria],
    summary="Municipios con su mercado de comercialización",
)
def listar_ciudades(service: UbicacionTarifaService = Depends(get_ubicacion_service)):
    return service.listar_ciudades()


@router.get(
    "/tarifa",
    response_model=TarifaUbicacionResponse,
    summary="Tarifa vigente de una vivienda: 24 h, monomía y componentes",
)
def get_tarifa(
    id_zona: int = Query(..., ge=1),
    cod_mercado: str = Query(..., max_length=30),
    estrato: int = Query(..., ge=1, le=6),
    fecha: Optional[date] = Query(None, description="Día a consultar. Default: hoy (America/Bogota)"),
    consumo_mensual_kwh: Optional[float] = Query(None, ge=0),
    service: UbicacionTarifaService = Depends(get_ubicacion_service),
):
    try:
        resultado = service.obtener_tarifa(id_zona, cod_mercado, estrato, fecha, consumo_mensual_kwh)
    except UbicacionNoEncontrada as e:
        raise HTTPException(status_code=404, detail=str(e))
    if resultado is None:
        raise HTTPException(
            status_code=404,
            detail="No hay tarifa publicada para esta ubicación en la fecha consultada",
        )
    return resultado


@router.get(
    "/calendario",
    response_model=CalendarioTarifasResponse,
    summary="Tarifas publicadas mes a mes en un año",
)
def get_calendario(
    id_zona: int = Query(..., ge=1),
    cod_mercado: str = Query(..., max_length=30),
    estrato: int = Query(..., ge=1, le=6),
    anio: int = Query(..., ge=2000, le=2100),
    consumo_mensual_kwh: Optional[float] = Query(None, ge=0),
    service: UbicacionTarifaService = Depends(get_ubicacion_service),
):
    try:
        resultado = service.obtener_calendario(id_zona, cod_mercado, estrato, anio, consumo_mensual_kwh)
    except UbicacionNoEncontrada as e:
        raise HTTPException(status_code=404, detail=str(e))
    if resultado is None:
        raise HTTPException(status_code=404, detail="No hay tarifas residenciales para esta ubicación")
    return resultado
