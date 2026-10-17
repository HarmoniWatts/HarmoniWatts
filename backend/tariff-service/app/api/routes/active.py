# app/api/routes/active.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional

from app.core.database import get_db
from app.repositories.postgres.cliente_repository import ClienteRepository
from app.services.active.tarifa_service import TarifaActivaService
from app.repositories.postgres.tarifa_repository import TarifaRepository
from app.services.active.tarifa_service import TarifaActivaService
from app.services.active.franja_service import FranjaService
from app.services.active.alerta_service import AlertaTarifaService
from app.services.business.tarifa_selector import TarifaSelector
from app.models.schemas.active_schemas import (
    TarifaActivaResponse,
    PreciosDiaResponse,
    FranjaActualResponse,
    ProximaFranjaAltaResponse,
)
from app.api.dependencies import (
    get_tarifa_repository,
    get_tarifa_selector,
    get_current_cliente,
    get_cliente_repository
)



router = APIRouter(prefix="/tariff/active", tags=["Tarifas Activas"])


# =====================================================
# Dependencias de servicios
# =====================================================
def get_tarifa_activa_service(
    repo: TarifaRepository = Depends(get_tarifa_repository),
    cliente_repo: ClienteRepository = Depends(get_cliente_repository),
    selector: TarifaSelector = Depends(get_tarifa_selector),
) -> TarifaActivaService:
    """Provee el servicio con todas sus dependencias."""
    return TarifaActivaService(
        repo=repo,
        cliente_repo=cliente_repo,
        selector=selector,
    )


def get_franja_service(
    repo: TarifaRepository = Depends(get_tarifa_repository),
    cliente_repo: ClienteRepository = Depends(get_cliente_repository),
    selector: TarifaSelector = Depends(get_tarifa_selector),
) -> FranjaService:
    """Provee el servicio con todas sus dependencias."""
    return FranjaService(
        repo=repo,
        cliente_repo=cliente_repo,
        selector=selector,
    )

def get_alerta_service(
    repo: TarifaRepository = Depends(get_tarifa_repository),
    cliente_repo: ClienteRepository = Depends(get_cliente_repository),
    selector: TarifaSelector = Depends(get_tarifa_selector),
) -> AlertaTarifaService:
    """Provee el servicio con todas sus dependencias."""
    return AlertaTarifaService(
        repo=repo,
        cliente_repo=cliente_repo,
        selector=selector,
    )



# =====================================================
# GET /current/{id_cliente}
# =====================================================
@router.get(
    "/current/{id_cliente}",
    response_model=TarifaActivaResponse,
    summary="Tarifa vigente completa del cliente"
)
def get_tarifa_current(
    id_cliente: int,
    fecha: Optional[date] = Query(None, description="Fecha de consulta"),
    consumo_mensual_kwh: Optional[float] = Query(None, description="Consumo mensual en kWh"),
    service: TarifaActivaService = Depends(get_tarifa_activa_service),
    # cliente_autenticado = Depends(get_current_cliente),
):
    """
    Obtiene la tarifa vigente completa de un cliente.
    
    Endpoint fino: delega toda la lógica al TarifaActivaService.
    """
    # if cliente_autenticado.id_cliente != id_cliente:       ← Comentado
    #     raise HTTPException(403, "No autorizado")
    print(f"solicitando tarifa para: {id_cliente}")
    # 1. Validar autorización
    # if cliente_autenticado.id_cliente != id_cliente:
    #     raise HTTPException(
    #         status_code=403,
    #         detail="No autorizado para consultar otro cliente"
    #     )
    
    # 2. Delegar al servicio
    resultado = service.obtener_tarifa_vigente(
        id_cliente=id_cliente,
        fecha=fecha,
        consumo_mensual_kwh=consumo_mensual_kwh
    )
    
    
    # 3. Manejar errores del servicio
    if resultado is None:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró tarifa vigente para el cliente {id_cliente}"
        )
    
    return resultado


# =====================================================
# GET /daily-bands/{id_cliente}
# =====================================================
@router.get(
    "/daily-bands/{id_cliente}",
    response_model=PreciosDiaResponse,
    summary="Precios de las 24 horas del día"
)
def get_daily_bands(
    id_cliente: int,
    fecha: Optional[date] = Query(None),
    consumo_mensual_kwh: Optional[float] = Query(None, description="Consumo mensual en kWh"),
    service: FranjaService = Depends(get_franja_service),
    # cliente_autenticado = Depends(get_current_cliente),
):
    """
    Precios de las 24 horas del día.
    
    Endpoint fino: delega la construcción de la curva al FranjaService.
    """
    # if cliente_autenticado.id_cliente != id_cliente:
    #     raise HTTPException(
    #         status_code=403,
    #         detail="No autorizado para consultar otro cliente"
    #     )
    
    resultado = service.obtener_precios_dia(
        id_cliente=id_cliente,
        fecha=fecha,
        consumo_mensual_kwh=consumo_mensual_kwh
    )
    
    if not resultado.get('precios'):
        raise HTTPException(
            status_code=404,
            detail=f"No se encontraron precios para el cliente {id_cliente}"
        )
    
    return resultado


# =====================================================
# GET /current-franja/{id_cliente}
# =====================================================
@router.get(
    "/current-franja/{id_cliente}",
    response_model=FranjaActualResponse,
    summary="Franja horaria actual y su precio"
)
def get_current_franja(
    id_cliente: int,
    hora: Optional[int] = Query(None, ge=1, le=24),
    consumo_mensual_kwh: Optional[float] = Query(None, description="Consumo mensual en kWh"),
    service: FranjaService = Depends(get_franja_service),
    # cliente_autenticado = Depends(get_current_cliente),
):
    """
    Franja horaria actual y su precio.
    
    Endpoint fino: delega la resolución hora→franja al FranjaService.
    """
    # if cliente_autenticado.id_cliente != id_cliente:
    #     raise HTTPException(
    #         status_code=403,
    #         detail="No autorizado para consultar otro cliente"
     #   )
    
    resultado = service.obtener_franja_actual(
        id_cliente=id_cliente,
        hora=hora,
        consumo_mensual_kwh=consumo_mensual_kwh
    )
    
    if resultado is None:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró franja actual para el cliente {id_cliente}"
        )
    
    return resultado


# =====================================================
# GET /high-franja/{id_cliente}
# =====================================================
@router.get(
    "/high-franja/{id_cliente}",
    response_model=ProximaFranjaAltaResponse,
    summary="Próxima ventana de alta tarifa relevante"
)
def get_high_franja(
    id_cliente: int,
    horizonte_horas: int = Query(12, ge=1, le=24),
    umbral_pico: bool = Query(True),
    consumo_mensual_kwh: Optional[float] = Query(None, description="Consumo mensual en kWh"),
    service: AlertaTarifaService = Depends(get_alerta_service),
    # cliente_autenticado = Depends(get_current_cliente),
):
    """
    Próxima ventana de alta tarifa.
    
    Endpoint fino: delega la detección y cálculo al AlertaTarifaService.
    """
    # if cliente_autenticado.id_cliente != id_cliente:
    #     raise HTTPException(
    #         status_code=403,
    #         detail="No autorizado para consultar otro cliente"
    #     )
    
    resultado = service.detectar_proxima_ventana_alta(
        id_cliente=id_cliente,
        horizonte_horas=horizonte_horas,
        umbral_punta=umbral_pico,
        consumo_mensual_kwh=consumo_mensual_kwh
    )
    
    if resultado is None:
        raise HTTPException(
            status_code=404,
            detail=f"No se pudo analizar tarifas para el cliente {id_cliente}"
        )
    
    return resultado