from fastapi import APIRouter, Depends, HTTPException
from app.repositories.sql_repo import SQLTarifasRepo
from app.repositories.mongo_repo import MongoTarifasRepo
from app.services.sincronizacion import sincronizar_pendientes
from app.services.pipeline import ejecutar
from app.repositories.enertotales.cliente import EnertotalesAPI
from app.config import settings
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/tarifas", tags=["tarifas"])


def get_sql_repo() -> SQLTarifasRepo:
    return SQLTarifasRepo()


def get_mongo_repo() -> MongoTarifasRepo:
    return MongoTarifasRepo()


@router.post("/ingest")
async def ingest(
    desde: str | None = None,
    sql_repo: SQLTarifasRepo = Depends(get_sql_repo),
):
    """Dispara la ingesta desde la API externa hacia SQL."""
    driver = EnertotalesAPI(
        base_url=settings.ENERTOTALES_BASE_URL,
        headers={"User-Agent": settings.HTTP_USER_AGENT},
    )
    filtros = settings.ENERTOTALES_FILTROS.split("|")
    resumen = ejecutar(driver, sql_repo, filtros, desde=desde)
    return resumen


@router.post("/sync")
async def sync(
    sql_repo: SQLTarifasRepo = Depends(get_sql_repo),
    mongo_repo: MongoTarifasRepo = Depends(get_mongo_repo),
):
    """Sincroniza SQL → Mongo las publicaciones pendientes."""
    return sincronizar_pendientes(sql_repo, mongo_repo)