# modules/forecast/estimator.py
from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Optional
import numpy as np
import pandas as pd
import asyncio

from .series import SeriesLoader
from .estructura import calcular_estructura

import structlog

logger = structlog.get_logger()

COMPONENTES_CU = ["Gm", "Tm", "Dm", "Cm", "PRm", "Rm"]
COMPONENTES    = COMPONENTES_CU + ["Cfmj"]
SERIES_MODELAR = COMPONENTES + ["monomia"]

# Selección del benchmark (congelada). Cambiar aquí si re-ejecutas el benchmark.
MODELO_POR_COMPONENTE = {
    "Gm": "Naive",
    "Tm": "Rev50",
    "Dm": "LightGBM",   # o "Rev50" si no quieres depender de lightgbm
    "Cm": "Rev50",
    "PRm": "Naive",
    "Rm": "Naive",
    "Cfmj": "ARIMA",    # o "Naive" si no quieres depender de statsmodels
    "monomia": "Naive",
}

K_ESTRUCTURA = 3
TOL_K = 0.005
MIN_TRAIN = 8

import asyncio
import threading
from concurrent.futures import Future

def _run_in_thread_with_loop(func, *args, **kwargs):
    """
    Ejecuta una función síncrona en un hilo separado que tiene su PROPIO event loop.
    Esto evita que aiohttp/pydataxm se queje de que no hay tarea, y evita
    bloquear el bucle de uvicorn.
    """
    result_future = Future()

    def target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Envolver la función síncrona en una corrutina
            async def wrapper():
                return func(*args, **kwargs)
            result = loop.run_until_complete(wrapper())
            result_future.set_result(result)
        except Exception as e:
            result_future.set_exception(e)
        finally:
            loop.close()

    t = threading.Thread(target=target)
    t.start()
    t.join()
    return result_future.result()


@dataclass
class EstimacionTarifa:
    mercado: str
    nivel_tension: str
    tipo_tarifa: str
    anio: int
    mes: int
    valores_franja: dict
    cu_base: float
    cu_aplicado: float
    componentes_cu: dict
    Cmfj: float
    meta: dict

    def to_dict(self) -> dict:
        """Forma exacta que pediste (sin meta, que va aparte)."""
        return {
            "mercado": self.mercado,
            "nivel_tension": self.nivel_tension,
            "tipo_tarifa": self.tipo_tarifa,
            "mes": self.mes,
            "anio": self.anio,
            "valores_franja": self.valores_franja,
            "cu_base": self.cu_base,
            "cu_aplicado": self.cu_aplicado,
            "componentes_cu": self.componentes_cu,
            "Cmfj": self.Cmfj,
        }


class TariffEstimator:
    """
    Estima la tarifa de un mes para (mercado, nivel, tipo) con el modelo híbrido
    ganador del benchmark. No persiste: devuelve EstimacionTarifa.
    """

    def __init__(self, serie_repo, franja_repo, exog_loader=None):
        self.series = SeriesLoader(serie_repo)    # trae histórico por (mercado, nivel, tipo)
        self.serie_repo = serie_repo
        self.franja_repo = franja_repo    # trae valores por franja históricos
        self.exog_loader = exog_loader    # opcional: exógenas mensuales (XM/TRM/ONI)
        
    def auditar_franjas(self,est, cu_base, r2_func=None, ratios_key="ratios", mostrar_faltantes=True):
        """
        Revisa paso a paso el cálculo de franjas para F1..F8 y devuelve el diccionario resultante.
        """
        if r2_func is None:
            r2_func = lambda x: round(x, 2)  # Reemplaza por tu función r2 real si ya está definida

        franjas = {}
        print(f"=== AUDITORÍA DE FRANJAS | cu_base = {cu_base!r} ===\n")

        if ratios_key not in est:
            print(f"[ERROR] No existe la clave '{ratios_key}' en 'est'. Claves: {list(est.keys())}")
            return {}

        ratios_dict = est[ratios_key]

        for i in range(1, 9):
            clave = f"F{i}"

            if clave in ratios_dict:
                ratio = ratios_dict[clave]
                try:
                    producto = ratio * cu_base
                    valor_final = r2_func(producto)
                    franjas[clave] = valor_final

                    print(f"[{clave}] ENCONTRADO")
                    print(f"  1. est['{ratios_key}']['{clave}'] = {ratio!r} ({type(ratio).__name__})")
                    print(f"  2. Producto ({ratio} * {cu_base}) = {producto!r}")
                    print(f"  3. r2(producto) = {valor_final!r}\n")
                except Exception as e:
                    franjas[clave] = None
                    print(f"[{clave}] ERROR AL CALCULAR: {e} (ratio={ratio!r}, cu_base={cu_base!r})\n")
            else:
                franjas[clave] = None
                if mostrar_faltantes:
                    print(f"[{clave}] NO EXISTE en est['{ratios_key}'] -> None\n")

        print("=== DICCIONARIO FINAL ===")
        for k, v in franjas.items():
            print(f"  {k}: {v!r}")

        return franjas


    # ---------- API pública ----------
    async def estimar(self, mercado: str, nivel: str, tipo: str, anio: int, mes: int,
                modelos: Optional[dict] = None) -> EstimacionTarifa:
        # logger.info(f"Estimando {mercado}/{nivel}/{tipo} {anio}-{mes:02d} con modelos={modelos}")
        modelos = modelos or MODELO_POR_COMPONENTE
        objetivo = pd.Timestamp(anio, mes, 1)

        serie = self.series.load(mercado, nivel, tipo)
        hist = serie[serie.index < objetivo]
        if len(hist) < MIN_TRAIN:
            raise ValueError(
                f"Histórico insuficiente antes de {objetivo:%Y-%m} "
                f"({len(hist)} meses, mínimo {MIN_TRAIN})"
            )
        
        # ✅ Ejecutar la carga de exógenas en un hilo con su propio bucle
        if self.exog_loader:
            exog = await asyncio.to_thread(
                _run_in_thread_with_loop, self.exog_loader.load
            )
        else:
            exog = None
        steps = (objetivo.year - hist.index[-1].year) * 12 + objetivo.month - hist.index[-1].month
        avisos = []
        if steps > 1:
            avisos.append(f"horizonte de {steps} meses: pronóstico recursivo, incertidumbre crece")

        pred = {}
        for c in SERIES_MODELAR:
            m = modelos.get(c, "Naive")
            try:
                pred[c] = self._predict_path(m, hist[c], exog, steps)[-1]
            except Exception as e:
                avisos.append(f"{c}: {m} falló ({type(e).__name__}); se usó Naive")
                pred[c] = float(hist[c].iloc[-1])

        cu_base = sum(pred[c] for c in COMPONENTES_CU)
        est = calcular_estructura(hist, self.franja_repo.get_franjas(mercado, nivel, tipo))

        if est["k_spread"] > TOL_K:
            cu_aplicado = pred["monomia"]
            metodo = "serie_propia"
            avisos.append("monomia no proporcional al CU base: pronosticada como serie propia")
        else:
            cu_aplicado = est["k_mon"] * cu_base
            metodo = "razon_al_CU"

        r2 = lambda v: round(float(v), 2)
        # franjas_calculadas = self.auditar_franjas(est, cu_base, r2_func=r2) # Usa tu r2 si ya existe
        franjas = {
            f"F{i}": (r2(est["ratios"][f"F{i}"] * cu_base) if f"F{i}" in est["ratios"] else None)
            for i in range(1, 9)
        }
        logger.info(f"Estimación {mercado}/{nivel}/{tipo} {anio}-{mes:02d}: método={metodo}, avisos={avisos}")
        # logger.debug(f"franjas={franjas}")
        return EstimacionTarifa(
            mercado=mercado,
            nivel_tension=self._label_nivel(nivel),
            tipo_tarifa=tipo,
            anio=anio,
            mes=mes,
            valores_franja=franjas,
            cu_base=r2(cu_base),
            cu_aplicado=r2(cu_aplicado),
            componentes_cu={
                "Gm": r2(pred["Gm"]), "Cm": r2(pred["Cm"]), "PR": r2(pred["PRm"]),
                "Dm": r2(pred["Dm"]), "Tm": r2(pred["Tm"]), "Rm": r2(pred["Rm"]),
            },
            Cmfj=r2(pred["Cfmj"]),
            meta={
                "modelos": {c: modelos.get(c, "Naive") for c in SERIES_MODELAR},
                "metodo_monomia": metodo,
                "config_horaria": est["config"],
                "meses_estructura": est["meses"],
                "avisos": avisos,
            },
        )

    # ---------- helpers ----------
    @staticmethod
    def _label_nivel(nivel: str) -> str:
        return {
            "N1_1": "N 1.1", "N1_2": "N 1.2", "N1_2_1_3": "N 1.2-1.3",
            "N1_2_50": "N 1.2-50", "N1_2_1_3_50": "N 1.2-1.3-50",
            "N2": "N 2", "N3": "N 3", "N4": "N 4",
        }.get(nivel, nivel)

    # def _get_series(self, mercado, nivel, tipo) -> pd.DataFrame:
    #     """DataFrame indexado por mes_ts con columnas SERIES_MODELAR + 'config' + 'interpolado'."""
    #     df = self.serie_repo.get_comp_series(mercado, nivel, tipo)
    #     if df.empty:
    #         raise ValueError(f"Sin histórico para {mercado}/{nivel}/{tipo}")
    #     idx = pd.date_range(df.index.min(), df.index.max(), freq="MS")
    #     df = df.reindex(idx)
    #     df["interpolado"] = df[COMPONENTES].isna().any(axis=1)
    #     df[SERIES_MODELAR] = df[SERIES_MODELAR].interpolate(limit=1, limit_area="inside")
    #     return df

    def _predict_path(self, name, y_hist, exog, steps):
        # Delega a models.py (Naive, Rev50, MA6, Drift3, LightGBM, ARIMA, ...)
        from .models import predict_path
        return predict_path(name, y_hist, exog, steps)

    # def _estructura(self, comp_hist, fr_hist, k=K_ESTRUCTURA):
    #     comp_hist = comp_hist[~comp_hist["interpolado"]].dropna(subset=COMPONENTES_CU + ["monomia"]).sort_index()
    #     cfg = comp_hist["config"].iloc[-1]
    #     d = comp_hist[comp_hist["config"] == cfg].tail(k)
    #     cu = d[COMPONENTES_CU].sum(axis=1)
    #     k_ser = d["monomia"] / cu
    #     spread = float((k_ser.max() - k_ser.min()) / k_ser.mean()) if len(d) > 1 else 0.0
    #     f = fr_hist[fr_hist.index.isin(d.index)].copy()
    #     f["ratio"] = f.apply(lambda r: r["valor"] / cu.loc[r.name], axis=1)
    #     return {
    #         "k_mon": float(k_ser.median()),
    #         "k_spread": spread,
    #         "ratios": f.groupby("franja")["ratio"].median().to_dict(),
    #         "config": cfg,
    #         "meses": len(d),
    #     }