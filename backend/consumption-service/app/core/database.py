from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings
import structlog

logger = structlog.get_logger()


class MongoDBManager:
    client: AsyncIOMotorClient = None
    database: AsyncIOMotorDatabase = None
    
    @classmethod
    async def connect(cls):
        """Establish connection to MongoDB"""
        logger.info("connecting_to_mongodb", host=settings.MONGODB_HOST)
        cls.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            maxPoolSize=50,
            minPoolSize=10,
            serverSelectionTimeoutMS=5000
        )
        cls.database = cls.client[settings.MONGODB_DATABASE]
        
        # Create indexes for performance
        await cls._create_indexes()
        logger.info("mongodb_connected")
    
    @classmethod
    async def _create_indexes(cls):
        """Create necessary indexes for fast queries"""
        collection = cls.database.consumptions
        
        # Índice compuesto para consultas por vivienda y timestamp
        await collection.create_index([
            ("household_id", 1),
            ("timestamp", -1)
        ])
        
        # Índice para consultas diarias
        await collection.create_index([
            ("household_id", 1),
            ("date", 1)
        ])
        
        # TTL para limpiar datos antiguos (opcional, 90 días)
        await collection.create_index(
            "timestamp",
            expireAfterSeconds=7776000  # 90 días
        )
        
        logger.info("database_indexes_created")
    
    @classmethod
    async def close(cls):
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
            logger.info("mongodb_disconnected")
    
    @classmethod
    def get_collection(cls, name: str):
        """Get a collection by name"""
        return cls.database[name]


async def get_database() -> AsyncIOMotorDatabase:
    """Dependency to get database"""
    return MongoDBManager.database