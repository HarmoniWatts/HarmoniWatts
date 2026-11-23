from datetime import datetime
from typing import Optional, Dict, Any, List
from bson import ObjectId
from loguru import logger

from app.core.database import MongoDBManager
from app.config import settings


class PredictionRepository:
    """Persistencia de predicciones en MongoDB."""
    
    def __init__(self):
        self.collection = MongoDBManager.get_collection(
            settings.MONGODB_COLLECTION_PREDICCIONES
        )
    
    async def guardar_prediccion(
        self,
        no_contrato: Optional[str],
        cod_retail: Optional[str],
        id_cliente: Optional[int],
        meter_no: Optional[str],
        horizonte_horas: int,
        predicciones: List[Dict[str, Any]],
        metadatos: Dict[str, Any],
    ) -> str:
        """Guarda una predicción en MongoDB."""
        doc = {
            "no_contrato": no_contrato,
            "cod_comercializadora": cod_retail,
            "id_cliente": id_cliente,
            "serie_medidor": meter_no,
            "fecha_generacion": datetime.utcnow(),
            "horizonte_horas": horizonte_horas,
            "predicciones": predicciones,
            "metadatos_prediccion": metadatos,
        }
        result = await self.collection.insert_one(doc)
        return str(result.inserted_id)
    
    async def obtener_ultima_prediccion(
        self,
        meter_no: str,
    ) -> Optional[Dict[str, Any]]:
        """Obtiene la última predicción de un medidor."""
        doc = await self.collection.find_one(
            {"id_medidor": meter_no},
            sort=[("fecha_generacion", -1)],
        )
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc
    
    async def listar_predicciones(
        self,
        meter_no: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Lista predicciones con paginación."""
        filtro = {"id_medidor": meter_no} if meter_no else {}
        
        total = await self.collection.count_documents(filtro)
        cursor = self.collection.find(filtro).sort("fecha_generacion", -1).skip(offset).limit(limit)
        items = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            items.append(doc)
        
        return {"total": total, "limit": limit, "offset": offset, "items": items}