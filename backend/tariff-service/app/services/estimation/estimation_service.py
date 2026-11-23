import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.modules.forecast.estimator import TariffEstimator
from app.modules.forecast.orchestrator import ForecastOrchestrator
from app.modules.forecast.exog import ExogLoader
from app.repositories.postgres.serie_repo import SerieRepo
from app.repositories.postgres.franja_repo import FranjaRepo
from app.repositories.postgres.tarifa_repository import TarifaRepository
from app.services.estimation.estimation_adapter import EstimationAdapter  # el de get_by_combinacion / upsert

import structlog

logger = structlog.get_logger()


class EstimationService:
    def __init__(self, db: Session, exog_loader: Optional[ExogLoader] = None):
        self.db = db
        self.serie_repo = SerieRepo(db)
        self.franja_repo = FranjaRepo(db)
        self.tarifa_repo = TarifaRepository(db)
        self.exog_loader = exog_loader or ExogLoader(hist_start=(2024, 10))  # default hist_start
        self.estimator = TariffEstimator(
            serie_repo=self.serie_repo,
            franja_repo=self.franja_repo,
            exog_loader=self.exog_loader,
        )
        self.adapter = EstimationAdapter(self.tarifa_repo)
        self.orchestrator = ForecastOrchestrator(estimator=self.estimator)

    async def estimar(
        self,
        comercializadora_cod: str,
        anio: int,
        mes: int,
        combinaciones: Optional[list[tuple[str, str, str]]] = None,
        modelos: Optional[dict] = None,
        persistir: bool = False,
    ) -> dict:
        resultado = await self.orchestrator.estimar_tarifas(
            comercializadora_cod=comercializadora_cod,
            anio=anio,
            mes=mes,
            combinaciones=combinaciones,
            modelos=modelos,
        )
        # logger.debug(f"Resultado de estimación: {resultado}")
        persistidas = 0
        if persistir and resultado["tarifas"]:
            persistidas = self._persistir_estimaciones(
                comercializadora_cod, anio, mes, resultado["tarifas"]
            )
        logger.info(f"Estimación completada: {len(resultado['tarifas'])} tarifas estimadas, {persistidas} persistidas.")
        return {
            "estado": "completado",
            "tarifas_estimadas": resultado["tarifas_estimadas"],
            "tarifas": resultado["tarifas"],
            "tarifas_persistidas": persistidas,
            "errores": resultado["errores"],
        }

    def _persistir_estimaciones(
        self,
        comercializadora_cod: str,
        anio: int,
        mes: int,
        tarifas: list[dict],
    ) -> int:
        """
        Inserta cada estimación como periodo_tarifario BORRADOR con:
          - fecha_calculo = NOW()
          - fecha_publicacion = NULL
          - observaciones = 'ESTIMADA v1 <modelos>'
          - numero_version = max(version existente)+1
        Usa el transformer y upsert existentes para mantener consistencia.
        """
        from app.services.extraction.tap_transformer import TAPTransformer  # tu transformer

        transformer = TAPTransformer()
        insertadas = 0
        for t in tarifas:
            try:
                tarifa_tap = self.adapter.to_tarifa_tap(t, comercializadora_cod)
                # upsert con force_new_version=True para no chocar con la PUBICADA
                ok = self.tarifa_repo.upsert_periodo_estimado(
                        tarifa_tap, modelos=t.get("meta", {}).get("modelos")
                    )
                if ok:
                    insertadas += 1
                    logger.info("Persistida estimación %s/%s/%s", t.get("mercado"), t.get("nivel_tension"), t.get("tipo_tarifa"))
                else:
                    logger.warning("No se persistió estimación %s/%s/%s: ya existe una versión publicada",
                                   t.get("mercado"), t.get("nivel_tension"), t.get("tipo_tarifa"))
            except Exception as e:
                logger.error("Error persistiendo estimación %s/%s/%s: %s",
                             t.get("mercado"), t.get("nivel_tension"), t.get("tipo_tarifa"), e)
        
        return insertadas