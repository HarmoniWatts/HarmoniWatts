from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from typing import Optional

from app.services.prediction_service import PredictionService
from app.services.model_loader import ModelLoader
from app.models.schemas.prediction_schemas import (
    PrediccionResponse,
    ContratoPrediccionRequest,
    BatchPrediccionRequest,
    BatchPrediccionResponse,
    ModelStatusResponse,
)
from app.core.exceptions import InsufficientHistoryError, ModelNotLoadedError
from app.config import settings


router = APIRouter(prefix="/prediction", tags=["Prediction"])


def get_prediction_service() -> PredictionService:
    return PredictionService()


# =====================================================
# GET /prediction/contrato/{no_contrato}/{cod_retail}
# =====================================================
@router.get("/contrato/{no_contrato}/{cod_retail}", response_model=PrediccionResponse)
async def predecir_contrat(
    no_contrato: str,
    cod_retail: str,
    id_cliente: Optional[int] = Query(None, description="ID del cliente (opcional)"),
    horizonte: int = Query(settings.HORIZONTE_HORAS, ge=24, le=168),
    persistir: bool = Query(True),
    service: PredictionService = Depends(get_prediction_service),
):
    """
    Genera el pronóstico de consumo horario para un medidor.
    
    Requiere al menos 504 h de historia horaria.
    """

    try:
        return await service.predecir_consumo_contrato(
            no_contrato=no_contrato,
            cod_retail=cod_retail,
            id_cliente=id_cliente,
            horizonte=horizonte,
            persistir=persistir,
        )
    except InsufficientHistoryError as e:
        raise HTTPException(404, str(e))
    except ModelNotLoadedError as e:
        raise HTTPException(503, str(e))
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        raise HTTPException(500, "Error interno del servicio")


# =====================================================
# GET /prediction/{meter_no}
# =====================================================
@router.get("/{meter_no}", response_model=PrediccionResponse)
async def predecir_meter(
    meter_no: str,
    horizonte: int = Query(settings.HORIZONTE_HORAS, ge=24, le=168),
    persistir: bool = Query(True),
    service: PredictionService = Depends(get_prediction_service),
):
    """
    Genera el pronóstico de consumo horario para un medidor.
    
    Requiere al menos 504 h de historia horaria.
    """
    try:
        return await service.predecir_medidor(
            meter_no=meter_no,
            horizonte=horizonte,
            persistir=persistir,
        )
    except InsufficientHistoryError as e:
        raise HTTPException(404, str(e))
    except ModelNotLoadedError as e:
        raise HTTPException(503, str(e))
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        raise HTTPException(500, "Error interno del servicio")


# =====================================================
# POST /prediction/batch
# =====================================================
@router.post("/batch", response_model=BatchPrediccionResponse)
async def predecir_batch(
    request: BatchPrediccionRequest,
    service: PredictionService = Depends(get_prediction_service),
):
    """
    Genera predicciones para múltiples medidores.
    
    Máximo 100 medidores por request.
    """
    try:
        return await service.predecir_batch(
            meters=request.meters,
            horizonte=request.horizonte,
            persistir=request.persistir,
        )
    except ModelNotLoadedError as e:
        raise HTTPException(503, str(e))
    except Exception as e:
        logger.error(f"Error inesperado en batch: {e}")
        raise HTTPException(500, "Error interno del servicio")


# =====================================================
# GET /prediction/model/status
# =====================================================
@router.get("/model/status", response_model=ModelStatusResponse)
async def model_status():
    """
    Consulta el estado del modelo cargado.
    """
    try:
        model = ModelLoader.get_model()
        return ModelStatusResponse(
            nombre="CentralFTForecaster",
            version=ModelLoader.get_version(),
            uri=ModelLoader.get_uri(),
            cargado=model is not None,
            horizonte_horas=settings.HORIZONTE_HORAS,
            min_history_horas=settings.MIN_HISTORY_H,
        )
    except ModelNotLoadedError:
        raise HTTPException(503, "Modelo no cargado")