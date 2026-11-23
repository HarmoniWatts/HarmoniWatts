# modules/forecast/orchestrator.py
import logging
from typing import List, Optional
from .estimator import TariffEstimator

import structlog

logger = structlog.get_logger()

class ForecastOrchestrator:
    def __init__(self, estimator: TariffEstimator):
        self.estimator = estimator

    async def estimar_tarifas(
        self,
        comercializadora_cod: str,
        anio: int,
        mes: int,
        combinaciones: Optional[List[tuple]] = None,
        modelos: Optional[dict] = None,
    ) -> dict:
        """
        Espejo de _procesar_pdfs: en vez de parsear PDFs, estima tarifas.

        Devuelve:
            {
            "estado": "completado",
            "tarifas_estimadas": int,
            "tarifas": List[dict],        # forma "Tarifa estimada"
            "errores": List[str],
            }
        """
        if combinaciones is None:
            # El repo debe exponer las combinaciones con histórico
            combinaciones = self.estimator.serie_repo.get_combinaciones(comercializadora_cod)

        tarifas: List[dict] = []
        errores: List[str] = []

        for mercado, nivel, tipo in combinaciones:
            try:
                est = await self.estimator.estimar(
                    mercado=mercado, nivel=nivel, tipo=tipo,
                    anio=anio, mes=mes, modelos=modelos,
                )
                tarifas.append(est.to_dict())
            except Exception as e:
                logger.error(f"Error estimando {mercado}/{nivel}/{tipo} {anio}-{mes:02d}: {e}")
                errores.append(f"{mercado}/{nivel}/{tipo}: {type(e).__name__}: {e}")

        logger.info(f"Estimadas {len(tarifas)} tarifas del mes {mes:02d}-{anio}, {len(errores)} errores")
                
        return {
            "estado": "completado", 
            "tarifas_estimadas": len(tarifas),
            "tarifas": tarifas,
            "errores": errores,
        }