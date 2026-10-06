from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.core.database import MongoDBManager
from app.core.sql import SQLManager
from app.api.routes import consumption, tarifas
import structlog

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida de la aplicación"""
    logger.info("starting_service", environment=settings.ENVIRONMENT)

    # SQL primario
    await SQLManager.connect()
    logger.info("sql_connected")

    # MongoDB secundario (cache/consulta)
    await MongoDBManager.connect()
    logger.info("mongo_connected")

    yield

    logger.info("shutting_down_service")
    await MongoDBManager.close()
    await SQLManager.close()
    logger.info("databases_disconnected")


app = FastAPI(
    title="HarmoniWatts Tarifas Service",
    description="Servicio de ingesta y consulta de tarifas energéticas",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.APP_NAME}


@app.get("/ready")
async def readiness_check():
    try:
        if MongoDBManager.client is None or SQLManager.engine is None:
            return {"status": "not_ready", "reason": "database_not_connected"}
        await MongoDBManager.client.admin.command("ping")
        with SQLManager.session() as s:
            s.execute("SELECT 1")
        return {"status": "ready"}
    except Exception as e:
        return {"status": "not_ready", "reason": str(e)}


app.include_router(consumption.router)
app.include_router(tarifas.router)


@app.get("/")
async def root():
    return {
        "service": "HarmoniWatts Tarifas Service",
        "version": "1.0.0",
        "endpoints": {
            "tarifas": "/api/v1/tarifas",
            "sync": "/api/v1/tarifas/sync",
        },
        "documentation": "/docs",
    }