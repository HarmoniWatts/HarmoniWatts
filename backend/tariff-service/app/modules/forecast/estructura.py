# modules/forecast/estructura.py
"""
Razones estructurales: monomia/CU y franja/CU.
Se calculan sobre los últimos K meses con la MISMA configuración horaria
que el último mes disponible. Las franjas siguen al CU base, no a la monomia.
"""
from __future__ import annotations
import pandas as pd

COMPONENTES_CU = ["Gm", "Tm", "Dm", "Cm", "PRm", "Rm"]
K_ESTRUCTURA = 3
TOL_K = 0.005


def calcular_estructura(
    comp_hist: pd.DataFrame,
    fr_hist: pd.DataFrame,
    k: int = K_ESTRUCTURA,
) -> dict:
    """
    comp_hist: DataFrame indexado por mes_ts, columnas COMPONENTES_CU + ['monomia','config','interpolado']
    fr_hist:   DataFrame indexado por mes_ts, columnas ['franja','valor']
    """
    comp_hist = (
        comp_hist[~comp_hist["interpolado"]]
        .dropna(subset=COMPONENTES_CU + ["monomia"])
        .sort_index()
    )
    if comp_hist.empty:
        raise ValueError("Sin histórico válido para calcular estructura")

    cfg = comp_hist["config"].iloc[-1]
    d = comp_hist[comp_hist["config"] == cfg].tail(k)
    if d.empty:
        raise ValueError(f"Sin meses con configuración {cfg} para estructura")

    cu = d[COMPONENTES_CU].sum(axis=1)
    k_ser = d["monomia"] / cu
    spread = float((k_ser.max() - k_ser.min()) / k_ser.mean()) if len(d) > 1 else 0.0

    f = fr_hist[fr_hist.index.isin(d.index)].copy()
    if f.empty:
        ratios = {}
    else:
        # cu por mes para el join
        cu_by_month = cu.to_dict()
        f["ratio"] = f.apply(lambda r: r["valor"] / cu_by_month[r.name], axis=1)
        ratios = f.groupby("franja")["ratio"].median().to_dict()

    return {
        "k_mon": float(k_ser.median()),
        "k_spread": spread,
        "ratios": ratios,
        "config": cfg,
        "meses": len(d),
    }