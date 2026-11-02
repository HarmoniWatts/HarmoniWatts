from datetime import datetime, date
from typing import Optional, List, Dict, Any
from loguru import logger
from bson import ObjectId

from app.core.database import MongoDBManager
from app.config import settings


class SyncRepository:
    """
    Repositorio para operaciones de sincronización.
    
    Persiste:
        - Registros de consumo en `consumos_enriquecidos`
        - Estado de sincronizaciones en `sync_estado`
        - Historial de sincronizaciones en `sync_historial`
    """
    
    def __init__(self):
        self.collection = MongoDBManager.get_collection(settings.MONGODB_COLLECTION_CONSUMOS)
        self.collection_estado = MongoDBManager.get_collection("sync_estado_consumos")
        self.collection_historial = MongoDBManager.get_collection("sync_historial_consumos")
    
    # =====================================================
    # CONSUMOS (upsert idempotente)
    # =====================================================
    
    async def upsert_consumo(self, documento: Dict[str, Any]) -> bool:
        """
        Upsert idempotente por (id_medidor, timestamp).
        
        Returns:
            True si insertó nuevo, False si actualizó o falló
        """
        try:
            filtro = {
                "id_medidor": documento["id_medidor"],
                "timestamp": documento["timestamp"],
            }
            
            resultado = await self.collection.update_one(
                filtro,
                {"$set": documento},
                upsert=True,
            )
            
            return resultado.upserted_id is not None
        except Exception as e:
            logger.error(f"Error en upsert_consumo: {e}")
            return False
    
    async def upsert_consumos_batch(
        self, documentos: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Upsert en lote con bulk_write.
        
        Returns:
            {'insertados': N, 'actualizados': M, 'errores': K}
        """
        from pymongo import UpdateOne
        
        if not documentos:
            return {"insertados": 0, "actualizados": 0, "errores": 0}
        
        operaciones = []
        for doc in documentos:
            filtro = {
                "id_medidor": doc["id_medidor"],
                "timestamp": doc["timestamp"],
            }
            operaciones.append(
                UpdateOne(filtro, {"$set": doc}, upsert=True)
            )
        
        try:
            resultado = await self.collection.bulk_write(operaciones, ordered=False)
            return {
                "insertados": resultado.upserted_count,
                "actualizados": resultado.modified_count,
                "errores": len(resultado.bulk_api_result.get("writeErrors", [])),
            }
        except Exception as e:
            import time
            # logger.error(f"Error en upsert_consumos_batch.....")
            # time.sleep(5)
            logger.error(f"Error en upsert_consumos_batch: {e}")
            return {"insertados": 0, "actualizados": 0, "errores": len(documentos)}
    
    # =====================================================
    # SYNC ESTADO
    # =====================================================
    
    async def crear_sync_estado(
        self,
        id_sincronizacion: str,
        meter_no: Optional[str],
        fecha_inicio: Optional[date],
        fecha_fin: Optional[date],
    ):
        await self.collection_estado.insert_one({
            "id_sincronizacion": id_sincronizacion,
            "meter_no": meter_no,
            "fecha_inicio": fecha_inicio.isoformat() if fecha_inicio else None,
            "fecha_fin": fecha_fin.isoformat() if fecha_fin else None,
            "estado": "pendiente",
            "registros_obtenidos": 0,
            "registros_insertados": 0,
            "registros_duplicados": 0,
            "errores": [],
            "creada_en": datetime.utcnow(),
        })
    
    async def actualizar_sync_estado(
        self,
        id_sincronizacion: str,
        **kwargs,
    ):
        kwargs["actualizada_en"] = datetime.utcnow()
        await self.collection_estado.update_one(
            {"id_sincronizacion": id_sincronizacion},
            {"$set": kwargs},
        )
    
    async def obtener_sync_estado(
        self, id_sincronizacion: str
    ) -> Optional[Dict[str, Any]]:
        return await self.collection_estado.find_one(
            {"id_sincronizacion": id_sincronizacion}
        )
    
    # =====================================================
    # SYNC HISTORIAL
    # =====================================================
    
    async def registrar_historial(
        self,
        id_sincronizacion: str,
        meter_no: Optional[str],
        estado: str,
        registros_obtenidos: int,
        registros_insertados: int,
        registros_duplicados: int,
        errores: List[str],
        duracion_seg: int,
    ):
        await self.collection_historial.insert_one({
            "id_sincronizacion": id_sincronizacion,
            "meter_no": meter_no,
            "estado": estado,
            "registros_obtenidos": registros_obtenidos,
            "registros_insertados": registros_insertados,
            "registros_duplicados": registros_duplicados,
            "errores": errores,
            "duracion_seg": duracion_seg,
            "fecha_sincronizacion": datetime.utcnow(),
        })
    
    async def obtener_historial(
        self, limit: int = 50, offset: int = 0
    ) -> Dict[str, Any]:
        total = await self.collection_historial.count_documents({})
        cursor = (
            self.collection_historial
            .find({})
            .sort("fecha_sincronizacion", -1)
            .skip(offset)
            .limit(limit)
        )
        items = await cursor.to_list(length=limit)
        return {"total": total, "limit": limit, "offset": offset, "items": items}