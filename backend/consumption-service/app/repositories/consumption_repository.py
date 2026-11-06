# app/repositories/consumption_repository.py

from collections import defaultdict

from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List, Union
from app.config import settings
from app.core.local_calendar import utc_range_for_local_calendar_day, local_hour_from_utc_timestamp
import structlog

logger = structlog.get_logger()

# Costo y precio de una lectura según el modo de la tarifa (MONOMIA o franja).
# Los documentos anteriores a la sincronización con INELCA solo traen
# `costo_total` / `precio_kwh`; se usan como respaldo.
_ES_MONOMIA = {"$eq": ["$tarifa_aplicada.modo", "MONOMIA"]}
COSTO_LECTURA = {
    "$ifNull": [
        {"$cond": [_ES_MONOMIA, "$tarifa_aplicada.costo_total_monomia", "$tarifa_aplicada.costo_total_franja"]},
        "$tarifa_aplicada.costo_total",
    ]
}
PRECIO_LECTURA = {
    "$ifNull": [
        {"$cond": [_ES_MONOMIA, "$tarifa_aplicada.precio_kwh_monomia", "$tarifa_aplicada.precio_kwh_franja"]},
        "$tarifa_aplicada.precio_kwh",
    ]
}


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
        no_contrat: Union[int, str],
        cod_retail: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene la lectura más reciente de consumo
        """
        # Convertir ID al tipo correcto
        no_contrat = str(no_contrat)
        
        cursor = self.collection.find(
            {"no_contrato": no_contrat, "cod_comercializadora": cod_retail}
        ).sort("timestamp", -1).limit(1)
        
        docs = await cursor.to_list(length=1)
        
        if docs:
            return docs[0]
        
        return None
    
    async def get_daily_total(
        self,
        no_contrat: Union[int, str],
        cod_retail: str,
        target_date: date,
        tz: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene el consumo total del día y estadísticas
        Incluye costo total sumando los costos de cada registro
        """
        no_contrat = str(no_contrat)

        start, end_exclusive = utc_range_for_local_calendar_day(target_date, tz)

        pipeline = [
            {
                "$match": {
                    "no_contrato": no_contrat,
                    "cod_comercializadora": cod_retail,
                    "timestamp": {"$gte": start, "$lt": end_exclusive},
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_consumption_kwh": {"$sum": "$valor_kwh"},
                    
                    "total_cost_cop": {"$sum": COSTO_LECTURA},
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
                        "no_contrato": no_contrat,
                        "cod_comercializadora": cod_retail,
                        "timestamp": {"$gte": start, "$lt": end_exclusive},
                        "valor_kwh": results[0]["peak_power_kw"],
                    }
                )
                if peak_doc:
                    peak_hour = local_hour_from_utc_timestamp(peak_doc["timestamp"], tz)
            
            results[0]["peak_hour"] = peak_hour
            return results[0]
        
        return None
    
    async def get_hourly_days_consumption(
        self,
        no_contrat: Union[int, str],
        cod_retail: str,
        start: datetime,
        end_exclusive: datetime,
        tz: str,
    ) -> List[Dict[str, Any]]:
        """
        Obtiene consumo por hora (0-23 = hora local en `tz`) dentro de
        [start, end_exclusive). Si la ventana abarca varios días, las
        horas y consumo se agrupan por día.
        """
        no_contrat = str(no_contrat)

        pipeline = [
            {
                "$match": {
                     "no_contrato": no_contrat,
                    "cod_comercializadora": cod_retail,
                    "timestamp": {"$gte": start, "$lt": end_exclusive},
                }
            },
            {
                "$group": {
                    "_id": {
                        "date": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": "$timestamp",
                                "timezone": "America/Bogota"
                            }
                        },
                        "hour": {
                            "$hour": {
                                "date": "$timestamp",
                                "timezone": "America/Bogota"
                            }
                        }
                    },
                    "consumption_kwh": {"$sum": "$valor_kwh"},
                    "total_cost": {"$sum": COSTO_LECTURA},
                    "tarifa_promedio": {"$avg": PRECIO_LECTURA},
                }
            },
            {
                "$sort": {
                    "_id.date": 1,
                    "_id.hour": 1
                }
            }
        ]
        
        logger.info(f"pipeline - {pipeline}\n")
        print("start =", start)
        print("end   =", end_exclusive)
        cursor = self.collection.aggregate(pipeline)
        results = await cursor.to_list(length=None)
        logger.info(f"results - {results}")
        daily_profiles = defaultdict(list)

        for result in results:
            date = result["_id"]["date"]
            hour = result["_id"]["hour"]

            daily_profiles[date].append({
                "hour": hour,
                "consumption_kwh": result["consumption_kwh"],
                "total_cost": result["total_cost"],
                "tarifa_promedio": result.get("tarifa_promedio")
            })

        # Completar horas faltantes
        for date in daily_profiles:
            existing = {item["hour"]: item for item in daily_profiles[date]}

            daily_profiles[date] = [
                existing.get(hour, {
                    "hour": hour,
                    "consumption_kwh": 0.0,
                    "total_cost": 0.0,
                    "tarifa_promedio": None
                })
                for hour in range(24)
            ]
            
        logger.info(f"daily_profiles - {daily_profiles}")

        return dict(sorted(daily_profiles.items()))
    
    
    async def get_hourly_consumption(
            self,
            no_contrat: Union[int, str],
            cod_retail: str,
            start: datetime,
            end_exclusive: datetime,
            tz: str,
        ) -> List[Dict[str, Any]]:
            """
            Obtiene consumo por hora (0-23 = hora local en `tz`) dentro de
            [start, end_exclusive). Si la ventana abarca varios días, las
            horas y consumo se agrupan por día.
            """
            no_contrat = str(no_contrat)
    
            pipeline = [
                {
                    "$match": {
                        "no_contrato": no_contrat,
                        "cod_comercializadora": cod_retail,
                        "timestamp": {"$gte": start, "$lt": end_exclusive},
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "hour": {
                                "$hour": {"date": "$timestamp", "timezone": tz},
                            }
                        },
                        "consumption_kwh": {"$sum": "$valor_kwh"},
                        "total_cost": {"$sum": COSTO_LECTURA},
                        "tarifa_promedio": {"$avg": PRECIO_LECTURA},
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
        no_contrat: Union[int, str],
        cod_retail: str,
        start_date: date,
        end_date: date,
        tz: str,
    ) -> Dict[str, Dict[str, float]]:
        """
        Obtiene consumo total por día en un rango
        Retorna dict con formato: {"2025-04-21": {"kwh": 12.5, "cost": 4500}}
        """
        no_contrat = str(no_contrat)

        range_start, _ = utc_range_for_local_calendar_day(start_date, tz)
        _, range_end_exclusive = utc_range_for_local_calendar_day(end_date, tz)

        pipeline = [
            {
                "$match": {
                    "no_contrato": no_contrat,
                    "cod_comercializadora": cod_retail,
                    "timestamp": {"$gte": range_start, "$lt": range_end_exclusive},
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$timestamp",
                            "timezone": tz,
                        }
                    },
                    "total_kwh": {"$sum": "$valor_kwh"},
                    "total_cost": {"$sum": COSTO_LECTURA},
                }
            },
            {
                # ✅ Ordenar por fecha para que la serie salga en orden cronológico
                "$sort": {"_id": 1} 
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
        no_contrat: Union[int, str],
        cod_retail: str,
        year: int,
        tz: str,
    ) -> Dict[int, Dict[str, float]]:
        """
        Obtiene consumo total por mes para un año
        """
        no_contrat = str(no_contrat)

        start_d = date(year, 1, 1)
        end_d = date(year, 12, 31)
        start_utc, _ = utc_range_for_local_calendar_day(start_d, tz)
        _, end_exclusive = utc_range_for_local_calendar_day(end_d, tz)

        pipeline = [
            {
                "$match": {
                    "no_contrato": no_contrat,
                    "cod_comercializadora": cod_retail,
                    "timestamp": {"$gte": start_utc, "$lt": end_exclusive},
                }
            },
            {
                "$group": {
                    "_id": {"$month": {"date": "$timestamp", "timezone": tz}},
                    "total_kwh": {"$sum": "$valor_kwh"},
                    "total_cost": {"$sum": COSTO_LECTURA},
                }
            },
            {
                # Ordenar por mes
                "$sort": {"_id": 1}
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
        no_contrat: Union[int, str],
        cod_retail: str,
        start_date: datetime,
        end_date: datetime,
        limit: int = 10000
    ) -> List[Dict[str, Any]]:
        """
        Obtiene registros de consumo en un rango de fechas
        """
        no_contrat = str(no_contrat)
        
        cursor = self.collection.find({
            "no_contrato": no_contrat,
            "cod_comercializadora": cod_retail,
            "timestamp": {"$gte": start_date, "$lte": end_date}
        }).sort("timestamp", 1).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    async def get_previous_day_total(
        self,
        no_contrat: Union[int, str],
        cod_retail: str,
        target_date: date,
        tz: str,
    ) -> Optional[float]:
        """
        Obtiene el consumo total del día anterior
        """
        previous_date = target_date - timedelta(days=1)
        daily_total = await self.get_daily_total(no_contrat, cod_retail, previous_date, tz)
        
        if daily_total:
            return daily_total["total_consumption_kwh"]
        
        return None
    
    async def get_week_average(
        self,
        no_contrat: Union[int, str],
        cod_retail: str,
        target_date: date,
        tz: str,
    ) -> Optional[float]:
        """
        Obtiene el consumo promedio de los últimos 7 días
        """
        end_date = target_date - timedelta(days=1)
        start_date = target_date - timedelta(days=7)
        range_start, _ = utc_range_for_local_calendar_day(start_date, tz)
        _, range_end_exclusive = utc_range_for_local_calendar_day(end_date, tz)

        pipeline = [
            {
                "$match": {
                    "no_contrato": no_contrat,
                    "cod_comercializadora": cod_retail,
                    "timestamp": {"$gte": range_start, "$lt": range_end_exclusive},
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