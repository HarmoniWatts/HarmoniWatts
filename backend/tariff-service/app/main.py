from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.core.database import PostgreSQLManager, lifespan as db_lifespan
from app.api.routes import (
    active,
    historical,
    extraction
)
import structlog

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona el ciclo de vida de la aplicación.
    Conecta a PostgreSQL al iniciar y cierra al terminar.
    """
    # Startup
    logger.info("starting_tariff_service", environment=settings.ENVIRONMENT)
    
    # Conectar a PostgreSQL
    PostgreSQLManager.connect()
    
    # Verificar conexión
    if not PostgreSQLManager.health_check():
        logger.error("postgresql_connection_failed")
        raise RuntimeError("No se pudo conectar a PostgreSQL")
    
    logger.info("postgresql_connected")
    
    yield
    
    # Shutdown
    logger.info("shutting_down_tariff_service")
    PostgreSQLManager.close()
    logger.info("postgresql_disconnected")


app = FastAPI(
    title="HarmoniWatts Tariff Service",
    description=(
        "Servicio de gestión de tarifas eléctricas. "
        "Incluye tarifas activas (PostgreSQL), históricas (MongoDB), "
        "simulaciones y extracción automática desde PDFs de comercializadoras."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# =====================================================
# CORS - Configuración para comunicación con frontend y otros servicios
# =====================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción: lista específica de orígenes
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)


# =====================================================
# HEALTH CHECKS
# =====================================================
@app.get("/health", tags=["Health"])
async def health_check():
    """Verifica que el servicio esté vivo"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "1.0.0"
    }


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """
    Verifica que el servicio esté listo para recibir tráfico.
    Comprueba la conexión a PostgreSQL.
    """
    try:
        if PostgreSQLManager.engine is None:
            return {
                "status": "not_ready",
                "reason": "database_not_connected"
            }
        
        # Verificar conexión con un ping
        is_healthy = PostgreSQLManager.health_check()
        
        if not is_healthy:
            return {
                "status": "not_ready",
                "reason": "database_ping_failed"
            }
        
        return {
            "status": "ready",
            "checks": {
                "postgresql": "ok"
            }
        }
    except Exception as e:
        logger.error("readiness_check_failed", error=str(e))
        return {
            "status": "not_ready",
            "reason": str(e)
        }


# =====================================================
# INCLUIR ROUTERS
# =====================================================

# Rutas de tarifas activas (PostgreSQL)
app.include_router(
    active.router,
    prefix="/api/v1",
    tags=["Tarifas Activas"]
)

# Rutas de tarifas históricas (MongoDB)
app.include_router(
    historical.router,
    prefix="/api/v1",
    tags=["Tarifas Históricas"]
)

# Rutas de extracción de PDFs
app.include_router(
    extraction.router,
    prefix="/api/v1",
    tags=["Extracción"]
)


# =====================================================
# ROOT
# =====================================================
@app.get("/", tags=["Root"])
async def root():
    """Endpoint raíz con información del servicio"""
    return {
        "service": "HarmoniWatts Tariff Service",
        "version": "1.0.0",
        "description": "Gestión de tarifas eléctricas activas, históricas y extracción",
        "endpoints": {
            "active_tariffs": {
                "current": "/api/v1/tariff/active/current/{id_cliente}",
                "daily_bands": "/api/v1/tariff/active/daily-bands/{id_cliente}",
                "current_franja": "/api/v1/tariff/active/current-franja/{id_cliente}",
                "assign": "/api/v1/tariff/active/assign",
                "sync": "/api/v1/tariff/active/sync"
            },
            "historical_tariffs": {
                "by_period": "/api/v1/tariff/historical/{anio}/{mes}",
                "trends": "/api/v1/tariff/historical/trends",
                "compare": "/api/v1/tariff/historical/compare",
                "export": "/api/v1/tariff/historical/export"
            },
            "extraction": {
                "manual": "/api/v1/tariff/extraction/manual",
                "automatic": "/api/v1/tariff/extraction/automatica",
                "schedule": "/api/v1/tariff/extraction/programar",
                "status": "/api/v1/tariff/extraction/estado/{task_id}"
            },
            "documentation": "/docs"
        }
    }