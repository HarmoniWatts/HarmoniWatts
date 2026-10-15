from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.core.database import MongoDBManager
from app.api.routes import consumption
import structlog

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida de la aplicación"""
    # Startup
    logger.info("starting_consumption_service", environment=settings.ENVIRONMENT)
    await MongoDBManager.connect()
    logger.info("database_connected")
    
    yield
    
    # Shutdown
    logger.info("shutting_down_consumption_service")
    await MongoDBManager.close()
    logger.info("database_disconnected")


app = FastAPI(
    title="HarmoniWatts Consumption Service",
    description="Servicio de ingesta y consulta de datos de consumo energético",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS - Configuración para comunicación con frontend y otros servicios
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción: lista específica de orígenes
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.APP_NAME}


@app.get("/ready")
async def readiness_check():
    """Verifica que el servicio esté listo para recibir tráfico"""
    try:
        # Verificar conexión a MongoDB
        if MongoDBManager.client is None:
            return {"status": "not_ready", "reason": "database_not_connected"}
        
        await MongoDBManager.client.admin.command('ping')
        return {"status": "ready"}
    except Exception as e:
        return {"status": "not_ready", "reason": str(e)}


# Incluir rutas del servicio de consumo
app.include_router(consumption.router)


@app.get("/")
async def root():
    return {
        "service": "HarmoniWatts Consumption Service",
        "version": "1.0.0",
        "endpoints": {
            "current_consumption": "/api/v1/consumption/current/{household_id}",
            "daily_total": "/api/v1/consumption/daily-total/{household_id}"
        },
        "documentation": "/docs"
    }