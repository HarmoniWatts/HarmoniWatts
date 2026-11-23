# modules/forecast/features.py
"""
Construcción de features para los modelos.
Regla de oro: en t solo se usa información hasta t-1 (sin fuga).
"""
from __future__ import annotations
import numpy as np
import pandas as pd

CORE = ["r_l1", "r_l2", "gap_ma3"]
SARIMAX_EXOG_DEFAULT = ["bolsa_mean", "embalse_pct", "oni", "trm_mean"]


def _design(y: pd.Series, exog: pd.DataFrame | None) -> tuple[pd.DataFrame, pd.Series]:
    """
    Devuelve (X, r):
      r = cambio logarítmico mensual en % (target de los modelos lineales/árboles)
      X = features: r_l1, r_l2, gap_ma3 + exógenas rezagadas (nivel y variación)
    """
    ly = np.log(y.clip(lower=1e-6))
    r = ly.diff() * 100
    X = pd.DataFrame(
        {
            "r_l1": r.shift(1),
            "r_l2": r.shift(2),
            "gap_ma3": (ly.shift(1) - ly.shift(1).rolling(3).mean()) * 100,
        },
        index=y.index,
    )
    return X.join(make_exog_features(exog, y.index)), r


def make_exog_features(exog: pd.DataFrame | None, idx: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Features de exógenas para los meses de `idx` usando solo información hasta t-1.
    - nivel rezagado:  x_l1 = x.shift(1)
    - variación:       x_d1 = x.shift(1) - x.shift(2)
    """
    if exog is None or exog.empty:
        return pd.DataFrame(index=idx)
    full = pd.date_range(
        min(exog.index.min(), idx.min()) - pd.DateOffset(months=2),
        max(exog.index.max(), idx.max()),
        freq="MS",
    )
    e = exog.reindex(full).ffill()
    lvl = e.shift(1).add_suffix("_l1")
    chg = (e.shift(1) - e.shift(2)).add_suffix("_d1")
    return pd.concat([lvl, chg], axis=1).reindex(idx)