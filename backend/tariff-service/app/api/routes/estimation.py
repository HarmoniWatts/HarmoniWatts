from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4
import logging

from app.core.database import get_db
from app.models.schemas.estimation_schemas import (
    EstimacionRequest,
    EstimacionResponse,
    EstimacionResultadoResponse,
)
from app.services.estimation.estimation_service import EstimationService
from app.services.estimation.estimation_state import EstimationStateStore
from app.modules.forecast.exog import ExogLoader

import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/tariff/estimation", tags=["Estimación"])


def get_estimation_service(db: Session = Depends(get_db)) -> EstimationService:
    # ExogLoader con caché por proceso; ajusta hist_start a tu primer mes con datos
    return EstimationService(db, exog_loader=ExogLoader(hist_start=(2024, 10)))


@router.post("/", response_model=EstimacionResponse)
async def estimar_tarifas_endpoint(
    request: EstimacionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    service: EstimationService = Depends(get_estimation_service),
):
    """Estima las tarifas de un mes con el modelo híbrido (Gm=Naive, Tm=Rev50, ...)."""

    id_estimacion = f"estim_{uuid4().hex[:8]}"

    EstimationStateStore.crear(
        id_estimacion=id_estimacion,
        datos_iniciales={
            "id_estimacion": id_estimacion,
            "anio": request.anio,
            "mes": request.mes,
            "comercializadora_cod": request.comercializadora_cod,
            "persistir": request.persistir,
        },
    )

    async def ejecutar_y_actualizar():

        try:
            EstimationStateStore.actualizar(id_estimacion, estado="en_proceso")

            resultado = await service.estimar(
                comercializadora_cod=request.comercializadora_cod,
                anio=request.anio,
                mes=request.mes,
                combinaciones=request.combinaciones,
                modelos=request.modelos,
                persistir=request.persistir,
            )

            EstimationStateStore.actualizar(
                id_estimacion,
                estado="completado",
                tarifas_estimadas=resultado.get("tarifas_estimadas", 0),
                tarifas_persistidas=resultado.get("tarifas_persistidas", 0),
                tarifas=resultado.get("tarifas", []),
                errores=resultado.get("errores", []),
                mensaje="Estimación completada",
            )
        except Exception as e:
            logger.error(f"Error en estimación {id_estimacion}: {e}")
            EstimationStateStore.actualizar(
                id_estimacion,
                estado="error",
                errores=[str(e)],
                mensaje=f"Error: {e}",
            )

    background_tasks.add_task(ejecutar_y_actualizar)

    return EstimacionResponse(
        id_estimacion=id_estimacion,
        estado="pendiente",
        anio=request.anio,
        mes=request.mes,
        comercializadora_cod=request.comercializadora_cod,
        mensaje="Estimación iniciada en segundo plano",
    )


@router.get("/{id_estimacion}", response_model=EstimacionResultadoResponse)
async def obtener_estimacion(id_estimacion: str):
    """Consulta el estado y, si terminó, las tarifas estimadas."""
    datos = EstimationStateStore.obtener(id_estimacion)
    if not datos:
        raise HTTPException(status_code=404, detail="Estimación no encontrada")
    return EstimacionResultadoResponse(**datos)