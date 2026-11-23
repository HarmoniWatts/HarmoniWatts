# modules/forecast/series.py
"""
Acceso a series históricas desde la BD (vía repositorio).
No hace SQL directo: delega al repo para mantener separación de capas.
"""
from __future__ import annotations
import logging
import pandas as pd

import structlog

logger = structlog.get_logger()

COMPONENTES_CU = ["Gm", "Tm", "Dm", "Cm", "PRm", "Rm"]
COMPONENTES    = COMPONENTES_CU + ["Cfmj"]
SERIES_MODELAR = COMPONENTES + ["monomia"]


class SeriesLoader:
    """
    Envuelve `serie_repo` para entregar un DataFrame listo para modelar:
      - indexado por mes_ts (freq MS)
      - columnas SERIES_MODELAR + 'config'
      - columna 'interpolado' (True si algún componente faltaba y se interpoló)
    """

    def __init__(self, serie_repo):
        self.serie_repo = serie_repo

    def load(self, mercado: str, nivel: str, tipo: str, avisar: bool = True) -> pd.DataFrame:
        df = self.serie_repo.get_comp_series(mercado, nivel, tipo)
        if df is None or df.empty:
            raise ValueError(f"Sin histórico para {mercado}/{nivel}/{tipo}")

        # Asegurar índice mensual continuo
        idx = pd.date_range(df.index.min(), df.index.max(), freq="MS")
        df = df.reindex(idx)

        # Marcar interpolados (antes de interpolar)
        df["interpolado"] = df[COMPONENTES].isna().any(axis=1)
        faltan = [i.strftime("%Y-%m") for i in df.index[df["interpolado"]]]
        if faltan and avisar:
            logger.warning(
                "Meses sin dato para %s/%s/%s: %s (se interpola 1 mes)",
                mercado, nivel, tipo, faltan,
            )

        # Interpolar solo huecos internos de 1 mes
        df[SERIES_MODELAR] = df[SERIES_MODELAR].interpolate(limit=1, limit_area="inside")
        return df