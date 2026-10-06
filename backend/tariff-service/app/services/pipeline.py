from datetime import date, datetime
from app.repositories.base import RepositorioTarifas
from app.repositories.sql_repo import SQLTarifasRepo
from app.services.seleccion import seleccionar_mas_recientes
from app.services.extraccion import extraer_tablas
from app.services.transformacion import tablas_a_tarifas
import structlog

logger = structlog.get_logger()


def ejecutar(
    driver: RepositorioTarifas,
    sql_repo: SQLTarifasRepo,
    filtros: list[str],
    desde: date | None = None,
) -> dict:
    """
    Ingesta desde la API externa hacia SQL (primario).
    Devuelve un resumen de lo procesado.
    """
    docs = list(driver.listar_documentos(filtros, desde))
    seleccion = seleccionar_mas_recientes(docs)

    resumen = {"nuevos": 0, "saltados": 0, "errores": 0, "meses": []}

    for (anio, mes), doc in sorted(seleccion.items()):
        if sql_repo.existe_publicacion(driver.comercializador, anio, mes):
            logger.info("publicacion_ya_existe",
                        comercializador=driver.comercializador,
                        anio=anio, mes=mes)
            resumen["saltados"] += 1
            continue

        try:
            pdf_bytes = driver.descargar_pdf(doc.url)
            tablas = extraer_tablas(pdf_bytes)
            tarifas = tablas_a_tarifas(
                tablas,
                comercializador=driver.comercializador,
                anio=anio, mes=mes,
                extraido_en=datetime.now(),
            )

            # Transacción SQL: todo o nada por publicación
            with sql_repo.transaction():
                n = sql_repo.guardar_tarifas(tarifas)
                sql_repo.marcar_publicacion_procesada(
                    driver.comercializador, anio, mes, n
                )

            logger.info("publicacion_guardada",
                        comercializador=driver.comercializador,
                        anio=anio, mes=mes, tarifas=n)
            resumen["nuevos"] += 1
            resumen["meses"].append(f"{anio}-{mes:02d}")

        except Exception as e:
            logger.error("error_procesando_publicacion",
                         comercializador=driver.comercializador,
                         anio=anio, mes=mes, error=str(e))
            resumen["errores"] += 1

    return resumen