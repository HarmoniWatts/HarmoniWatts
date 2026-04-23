from celery import Task
from tasks.celery_app import celery_app
from app.services.ingestion.smart_meter_client import SmartMeterClient
from app.repositories.consumption_repository import ConsumptionRepository
from app.core.database import MongoDBManager
from app.models.consumption import ConsumptionRecord
import structlog
from datetime import datetime, timedelta
import asyncio

logger = structlog.get_logger()


class IngestionTask(Task):
    _db_manager = None
    
    @property
    def db_manager(self):
        if self._db_manager is None:
            self._db_manager = MongoDBManager
        return self._db_manager


@celery_app.task(base=IngestionTask, bind=True, name="tasks.ingestion_tasks.sync_smart_meter_data")
def sync_smart_meter_data(self):
    """Sincroniza datos desde smart meters"""
    loop = asyncio.get_event_loop()
    if loop.is_running():
        result = asyncio.run(self._sync_data())
    else:
        result = loop.run_until_complete(self._sync_data())
    return result


async def _sync_data(self):
    """Implementación asíncrona de sincronización"""
    try:
        await MongoDBManager.connect()
        
        repository = ConsumptionRepository(MongoDBManager.database)
        client = SmartMeterClient()
        
        # Obtener lista de smart meters activos
        meters = await client.get_active_meters()
        
        saved_count = 0
        
        for meter in meters:
            # Obtener lecturas desde la última sincronización
            last_reading = await repository.get_latest_reading(meter.household_id)
            start_time = last_reading.timestamp if last_reading else datetime.utcnow() - timedelta(days=1)
            
            readings = await client.get_readings(meter.id, start_time, datetime.utcnow())
            
            for reading in readings:
                record = ConsumptionRecord(
                    household_id=meter.household_id,
                    timestamp=reading.timestamp,
                    consumption_kw=reading.power_kw,
                    consumption_kwh=reading.energy_kwh,
                    source="smart_meter"
                )
                await repository.upsert_consumption(record)
                saved_count += 1
        
        await MongoDBManager.close()
        
        return {
            "status": "success",
            "meters_processed": len(meters),
            "records_saved": saved_count
        }
        
    except Exception as e:
        logger.error("sync_failed", error=str(e))
        await MongoDBManager.close()
        raise self.retry(exc=e, countdown=60, max_retries=3)