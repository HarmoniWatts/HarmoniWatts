from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from app.api.dependencies import get_pdf_downloader
from app.core.database import get_db
from app.models.schemas.extraction_schemas import (
    ExtraccionManualRequest,
    ExtraccionAutomaticaRequest,
    ExtraccionResponse
)
from app.services.extraction.extraction_service import ExtractionService
# from app.tasks.extraction_tasks import extraer_tarifas_automatica

router = APIRouter(prefix="/tariff/extraction", tags=["Extracción"])


@router.post("/manual", response_model=ExtraccionResponse)
async def extraccion_manual(
    request: ExtraccionManualRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    downloader = Depends(get_pdf_downloader)
):
    """
    Extracción manual de tarifas desde PDFs de la comercializadora.
    El usuario especifica el rango de fechas.
    """
    service = ExtractionService(db, downloader)
    
    # Ejecutar en background para no bloquear
    background_tasks.add_task(
        service.extraer_manual,
        request.comercializadora_id,
        request.fecha_inicio,
        request.fecha_fin
    )
    
    return ExtraccionResponse(
        id_extraccion=f"manual_{date.today().isoformat()}",
        estado="pendiente",
        modo="manual",
        fecha_inicio=request.fecha_inicio,
        fecha_fin=request.fecha_fin,
        mensaje="Extracción manual iniciada en segundo plano"
    )


# @router.post("/automatica", response_model=ExtraccionResponse)
# async def extraccion_automatica(
#     request: ExtraccionAutomaticaRequest,
#     db: Session = Depends(get_db),
#     downloader = Depends(get_pdf_downloader)
# ):
#     """
#     Extracción automática de la última tarifa.
#     Se puede programar como tarea periódica (semanal/mensual).
#     """
#     # Disparar tarea Celery
#     task = extraer_tarifas_automatica.delay(request.comercializadora_id)
    
#     return ExtraccionResponse(
#         id_extraccion=task.id,
#         estado="pendiente",
#         modo="automatica",
#         mensaje=f"Tarea automática iniciada: {task.id}"
#     )


@router.post("/programar", response_model=dict)
async def programar_extraccion(
    request: ExtraccionAutomaticaRequest,
    db: Session = Depends(get_db)
):
    """
    Programa una extracción automática recurrente (semanal/mensual).
    Usa Celery Beat para ejecutar periódicamente.
    """
    # Guardar configuración en BD
    config = {
        "comercializadora_id": request.comercializadora_id,
        "frecuencia": request.frecuencia.value,
        "activa": request.activa,
        "proxima_ejecucion": None
    }
    
    # Registrar en Celery Beat (dinámicamente)
    # ... lógica de scheduling ...
    
    return {
        "estado": "programado",
        "frecuencia": request.frecuencia.value,
        "comercializadora_id": request.comercializadora_id
    }


@router.get("/estado/{task_id}", response_model=dict)
async def consultar_estado(task_id: str):
    """Consulta el estado de una tarea de extracción"""
    from app.core.celery_app import celery_app
    
    task = celery_app.AsyncResult(task_id)
    
    return {
        "task_id": task_id,
        "estado": task.state,
        "resultado": task.result if task.ready() else None
    }