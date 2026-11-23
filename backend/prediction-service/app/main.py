from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.core.database import MongoDBManager
from app.core.http_client import HTTPClientManager
from app.services.model_loader import ModelLoader
from app.api.routes import prediction


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("starting_prediction_service", env=settings.ENVIRONMENT)
    
    # Conexiones
    await MongoDBManager.connect()
    await HTTPClientManager.connect()
    logger.info("mongodb_and_http_connected")
    
    # Cargar modelo
    try:
        ModelLoader.load()
        logger.info("model_loaded", uri=settings.MLFLOW_MODEL_URI)
    except Exception as e:
        logger.error(f"Error cargando modelo: {e}")
        raise RuntimeError("No se pudo cargar el modelo") from e
    
    yield
    
    # Cierre
    logger.info("shutting_down_prediction_service")
    await HTTPClientManager.close()
    await MongoDBManager.close()


app = FastAPI(
    title="HarmoniWatts Prediction Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prediction.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "model_uri": settings.MLFLOW_MODEL_URI,
    }


@app.get("/ready")
async def ready():
    if ModelLoader.get_model() is None:
        return {"status": "not_ready", "reason": "model_not_loaded"}
    if MongoDBManager.client is None:
        return {"status": "not_ready", "reason": "mongodb_not_connected"}
    return {"status": "ready"}