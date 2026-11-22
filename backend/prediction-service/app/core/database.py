from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings
from loguru import logger


class MongoDBManager:
    client: AsyncIOMotorClient = None
    database: AsyncIOMotorDatabase = None
    
    @classmethod
    async def connect(cls):
        logger.info("connecting_to_mongodb", host=settings.MONGODB_URL)
        cls.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            maxPoolSize=50,
            minPoolSize=10,
            serverSelectionTimeoutMS=5000,
        )
        cls.database = cls.client[settings.MONGODB_DATABASE]
        await cls._create_indexes()
        logger.info("mongodb_connected")
    
    @classmethod
    async def _create_indexes(cls):
        col = cls.database[settings.MONGODB_COLLECTION_PREDICCIONES]
        # Consultas por medidor y fecha de generación
        await col.create_index([("id_medidor", 1), ("fecha_generacion", -1)])
        # Índice único para idempotencia (opcional)
        await col.create_index([("id_medidor", 1), ("horizonte_horas", 1)], unique=False)
        logger.info("mongodb_indexes_created")
    
    @classmethod
    async def close(cls):
        if cls.client:
            cls.client.close()
            logger.info("mongodb_disconnected")
    
    @classmethod
    def get_collection(cls, name: str):
        return cls.database[name]


async def get_database() -> AsyncIOMotorDatabase:
    return MongoDBManager.database