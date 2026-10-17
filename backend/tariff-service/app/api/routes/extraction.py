from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, logger
from sqlalchemy.orm import Session
from datetime import date
from uuid import uuid4

from app.api.dependencies import get_pdf_downloader
from app.core.database import get_db
from app.models.schemas.extraction_schemas import (
    ExtraccionManualRequest,
    ExtraccionAutomaticaRequest,
    ExtraccionResponse
)
from app.services.extraction.extraction_service import ExtractionService
from app.services.extraction.extraction_state import ExtractionStateStore

# from app.tasks.extraction_tasks import extraer_tarifas_automatica

router = APIRouter(prefix="/tariff/extraction", tags=["Extracción"])


@router.post("/manual", response_model=ExtraccionResponse)
async def extraccion_manual(
    request: ExtraccionManualRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    downloader = Depends(get_pdf_downloader)
):
    """Extracción manual de tarifas desde PDFs."""
    
    # Generar ID único
    id_extraccion = f"manual_{uuid4().hex[:8]}"
    
    # Registrar en el store
    ExtractionStateStore.crear(
        id_extraccion=id_extraccion,
        datos_iniciales={
            'id_extraccion': id_extraccion,
            'modo': 'manual',
            'fecha_inicio': request.fecha_inicio.isoformat(),
            'fecha_fin': request.fecha_fin.isoformat(),
            'comercializadora_cod': request.comercializadora_cod,
        }
    )
    
    # Crear el servicio
    service = ExtractionService(db, downloader)
    
    # Wrapper que actualiza el estado al terminar
    async def ejecutar_y_actualizar():
        try:
            ExtractionStateStore.actualizar(
                id_extraccion, estado='en_proceso'
            )
            
            resultado = await service.extraer_manual(
                request.comercializadora_cod,
                request.fecha_inicio,
                request.fecha_fin
            )
            
            ExtractionStateStore.actualizar(
                id_extraccion,
                estado='completado',
                tarifas_extraidas=resultado.get('tarifas_extraidas', 0),
                tarifas_insertadas=resultado.get('tarifas_insertadas', 0),
                errores=resultado.get('errores', []),
                mensaje='Extracción completada',
            )
            
        except Exception as e:
            logger.error(f"Error en extracción {id_extraccion}: {e}")
            ExtractionStateStore.actualizar(
                id_extraccion,
                estado='error',
                errores=[str(e)],
                mensaje=f'Error: {e}',
            )
    
    # Ejecutar en background
    background_tasks.add_task(ejecutar_y_actualizar)
    
    # Responder inmediatamente
    return ExtraccionResponse(
        id_extraccion=id_extraccion,
        estado='pendiente',
        modo='manual',
        fecha_inicio=request.fecha_inicio,
        fecha_fin=request.fecha_fin,
        mensaje='Extracción iniciada en segundo plano',
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
#     task = extraer_tarifas_automatica.delay(request.comercializadora_cod)
    
#     return ExtraccionResponse(
#         id_extraccion=task.id,
#         estado="pendiente",
#         modo="automatica",
#         mensaje=f"Tarea automática iniciada: {task.id}"
#     )


# @router.post("/programar", response_model=dict)
# async def programar_extraccion(
#     request: ExtraccionAutomaticaRequest,
#     db: Session = Depends(get_db)
# ):
#     """
#     Programa una extracción automática recurrente (semanal/mensual).
#     Usa Celery Beat para ejecutar periódicamente.
#     """
#     # Guardar configuración en BD
#     config = {
#         "comercializadora_cod": request.comercializadora_cod,
#         "frecuencia": request.frecuencia.value,
#         "activa": request.activa,
#         "proxima_ejecucion": None
#     }
    
#     # Registrar en Celery Beat (dinámicamente)
#     # ... lógica de scheduling ...
    
#     return {
#         "estado": "programado",
#         "frecuencia": request.frecuencia.value,
#         "comercializadora_cod": request.comercializadora_cod
#     }


# @router.get("/estado/{task_id}", response_model=dict)
# async def consultar_estado(task_id: str):
#     """Consulta el estado de una tarea de extracción"""
#     from app.core.celery_app import celery_app
    
#     task = celery_app.AsyncResult(task_id)
    
#     return {
#         "task_id": task_id,
#         "estado": task.state,
#         "resultado": task.result if task.ready() else None
#     }

# app/api/routes/extraction.py

@router.get("/estado/{id_extraccion}", response_model=ExtraccionResponse)
async def consultar_estado_extraccion(id_extraccion: str):
    """
    Consulta el estado de una extracción.
    
    El cliente hace polling cada X segundos hasta que el estado
    sea 'completado' o 'error'.
    """
    estado = ExtractionStateStore.obtener(id_extraccion)
    
    if not estado:
        raise HTTPException(
            status_code=404,
            detail=f"Extracción no encontrada: {id_extraccion}"
        )
    
    return ExtraccionResponse(
        id_extraccion=estado['id_extraccion'],
        estado=estado['estado'],
        modo=estado['modo'],
        fecha_inicio=estado.get('fecha_inicio'),
        fecha_fin=estado.get('fecha_fin'),
        tarifas_extraidas=estado.get('tarifas_extraidas', 0),
        tarifas_insertadas=estado.get('tarifas_insertadas', 0),
        errores=estado.get('errores', []),
        mensaje=estado.get('mensaje', ''),
    )