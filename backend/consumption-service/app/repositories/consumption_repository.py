# app/repositories/consumption_repository.py

from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List, Union
from app.models.consumption import ConsumoEnriquecido, ConsumoTimeSeries
from app.config import settings
import structlog

logger = structlog.get_logger()


class ConsumptionRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        # Usar colección principal o alterna según configuración
        self.collection_name = settings.CONSUMPTION_COLLECTION
        if settings.USE_ALT_COLLECTION:
            self.collection_name = settings.CONSUMPTION_ALT_COLLECTION
        
        self.collection = db[self.collection_name]
    
    async def get_latest_reading(
        self, 
        household_id: Union[int, str]
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene la lectura más reciente de consumo
        """
        # Convertir ID al tipo correcto
        if settings.HOUSEHOLD_ID_TYPE == "int":
            household_id = int(household_id)
        
        cursor = self.collection.find(
            {"id_vivienda": household_id}
        ).sort("timestamp", -1).limit(1)
        
        docs = await cursor.to_list(length=1)
        
        if docs:
            return docs[0]
        
        return None
    
    async def get_daily_total(
        self,
        household_id: Union[int, str],
        target_date: date
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene el consumo total del día y estadísticas
        Incluye costo total sumando los costos de cada registro
        """
        if settings.HOUSEHOLD_ID_TYPE == "int":
            household_id = int(household_id)
        
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())
        
        pipeline = [
            {
                "$match": {
                    "id_vivienda": household_id,
                    "timestamp": {"$gte": start, "$lte": end}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_consumption_kwh": {"$sum": "$valor_kwh"},
                    "total_cost_cop": {"$sum": "$tarifa_aplicada.costo_total"},
                    "average_power_kw": {"$avg": "$valor_kwh"},
                    "peak_power_kw": {"$max": "$valor_kwh"},
                    "readings_count": {"$sum": 1}
                }
            }
        ]
        
        results = await self.collection.aggregate(pipeline).to_list(length=1)
        
        if results:
            # Obtener hora del pico
            peak_hour = None
            if results[0].get("peak_power_kw"):
                peak_doc = await self.collection.find_one(
                    {
                        "id_vivienda": household_id,
                        "timestamp": {"$gte": start, "$lte": end},
                        "valor_kwh": results[0]["peak_power_kw"]
                    }
                )
                if peak_doc:
                    peak_hour = peak_doc["timestamp"].hour
            
            results[0]["peak_hour"] = peak_hour
            return results[0]
        
        return None
    
    async def get_hourly_consumption(
        self,
        household_id: Union[int, str],
        target_date: date
    ) -> List[Dict[str, Any]]:
        """
        Obtiene consumo por hora para un día
        """
        if settings.HOUSEHOLD_ID_TYPE == "int":
            household_id = int(household_id)
        
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())
        
        pipeline = [
            {
                "$match": {
                    "id_vivienda": household_id,
                    "timestamp": {"$gte": start, "$lte": end}
                }
            },
            {
                "$group": {
                    "_id": {"hour": {"$hour": "$timestamp"}},
                    "consumption_kwh": {"$sum": "$valor_kwh"},
                    "total_cost": {"$sum": "$tarifa_aplicada.costo_total"},
                    "tarifa_promedio": {"$avg": "$tarifa_aplicada.precio_kwh"}
                }
            },
            {"$sort": {"_id.hour": 1}}
        ]
        
        cursor = self.collection.aggregate(pipeline)
        results = await cursor.to_list(length=24)
        
        # Inicializar array de 24 horas
        hourly = []
        for hour in range(24):
            hourly.append({
                "hour": hour,
                "consumption_kwh": 0.0,
                "total_cost": 0.0,
                "tarifa_promedio": None
            })
        
        for result in results:
            hour = result["_id"]["hour"]
            hourly[hour] = {
                "hour": hour,
                "consumption_kwh": result["consumption_kwh"],
                "total_cost": result["total_cost"],
                "tarifa_promedio": result.get("tarifa_promedio")
            }
        
        return hourly
    
    async def get_daily_totals(
        self,
        household_id: Union[int, str],
        start_date: date,
        end_date: date
    ) -> Dict[str, Dict[str, float]]:
        """
        Obtiene consumo total por día en un rango
        Retorna dict con formato: {"2025-04-21": {"kwh": 12.5, "cost": 4500}}
        """
        if settings.HOUSEHOLD_ID_TYPE == "int":
            household_id = int(household_id)
        
        pipeline = [
            {
                "$match": {
                    "id_vivienda": household_id,
                    "timestamp": {
                        "$gte": datetime.combine(start_date, datetime.min.time()),
                        "$lte": datetime.combine(end_date, datetime.max.time())
                    }
                }
            },
            {
                "$group": {
                    "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                    "total_kwh": {"$sum": "$valor_kwh"},
                    "total_cost": {"$sum": "$tarifa_aplicada.costo_total"}
                }
            }
        ]
        
        cursor = self.collection.aggregate(pipeline)
        results = await cursor.to_list(length=None)
        
        return {
            item["_id"]: {"kwh": item["total_kwh"], "cost": item["total_cost"]}
            for item in results
        }
    
    async def get_monthly_totals(
        self,
        household_id: Union[int, str],
        year: int
    ) -> Dict[int, Dict[str, float]]:
        """
        Obtiene consumo total por mes para un año
        """
        if settings.HOUSEHOLD_ID_TYPE == "int":
            household_id = int(household_id)
        
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31, 23, 59, 59)
        
        pipeline = [
            {
                "$match": {
                    "id_vivienda": household_id,
                    "timestamp": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": {"$month": "$timestamp"},
                    "total_kwh": {"$sum": "$valor_kwh"},
                    "total_cost": {"$sum": "$tarifa_aplicada.costo_total"}
                }
            }
        ]
        
        cursor = self.collection.aggregate(pipeline)
        results = await cursor.to_list(length=None)
        
        return {
            item["_id"]: {"kwh": item["total_kwh"], "cost": item["total_cost"]}
            for item in results
        }
    
    async def get_consumption_by_date_range(
        self,
        household_id: Union[int, str],
        start_date: datetime,
        end_date: datetime,
        limit: int = 10000
    ) -> List[Dict[str, Any]]:
        """
        Obtiene registros de consumo en un rango de fechas
        """
        if settings.HOUSEHOLD_ID_TYPE == "int":
            household_id = int(household_id)
        
        cursor = self.collection.find({
            "id_vivienda": household_id,
            "timestamp": {"$gte": start_date, "$lte": end_date}
        }).sort("timestamp", 1).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    async def get_previous_day_total(
        self,
        household_id: Union[int, str],
        target_date: date
    ) -> Optional[float]:
        """
        Obtiene el consumo total del día anterior
        """
        previous_date = target_date - timedelta(days=1)
        daily_total = await self.get_daily_total(household_id, previous_date)
        
        if daily_total:
            return daily_total["total_consumption_kwh"]
        
        return None
    
    async def get_week_average(
        self,
        household_id: Union[int, str],
        target_date: date
    ) -> Optional[float]:
        """
        Obtiene el consumo promedio de los últimos 7 días
        """
        end_date = target_date - timedelta(days=1)
        start_date = target_date - timedelta(days=7)
        
        pipeline = [
            {
                "$match": {
                    "id_vivienda": household_id,
                    "timestamp": {
                        "$gte": datetime.combine(start_date, datetime.min.time()),
                        "$lte": datetime.combine(end_date, datetime.max.time())
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "avg_daily_kwh": {"$avg": "$valor_kwh"}
                }
            }
        ]
        
        results = await self.collection.aggregate(pipeline).to_list(length=1)
        
        if results:
            return results[0]["avg_daily_kwh"]
        
        return None