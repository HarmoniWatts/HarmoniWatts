import schedule, time
from datetime import date
from app.config import settings
from app.repositories.enertotales.cliente import EnertotalesAPI
from app.repositories.sql_repo import SQLTarifasRepo
from app.repositories.mongo_repo import MongoTarifasRepo
from app.services.pipeline import ejecutar
from app.services.sincronizacion import sincronizar_pendientes


def job_ingesta():
    """Semanal: trae nuevas publicaciones a SQL."""
    driver = EnertotalesAPI(
        base_url=settings.ENERTOTALES_BASE_URL,
        headers={"User-Agent": settings.HTTP_USER_AGENT},
    )
    filtros = settings.ENERTOTALES_FILTROS.split("|")
    hoy = date.today()
    desde = date(hoy.year, hoy.month, 1)
    ejecutar(driver, SQLTarifasRepo(), filtros, desde=desde)


def job_sync():
    """Diario: replica SQL → Mongo lo que esté pendiente."""
    sincronizar_pendientes(SQLTarifasRepo(), MongoTarifasRepo())


if __name__ == "__main__":
    # Backfill inicial
    if settings.BACKFILL_ACTIVO:
        driver = EnertotalesAPI(
            base_url=settings.ENERTOTALES_BASE_URL,
            headers={"User-Agent": settings.HTTP_USER_AGENT},
        )
        filtros = settings.ENERTOTALES_FILTROS.split("|")
        desde = date.fromisoformat(settings.BACKFILL_DESDE)
        ejecutar(driver, SQLTarifasRepo(), filtros, desde=desde)
        sincronizar_pendientes(SQLTarifasRepo(), MongoTarifasRepo())

    # Programación
    schedule.every().monday.at("06:00").do(job_ingesta)
    schedule.every().day.at("06:30").do(job_sync)   # sync más frecuente

    while True:
        schedule.run_pending()
        time.sleep(30)