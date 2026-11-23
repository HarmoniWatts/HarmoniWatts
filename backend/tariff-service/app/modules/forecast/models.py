# modules/forecast/models.py
"""
Modelos del benchmark. Reentrenan al vuelo; no hay pesos persistidos.
`predict_path` devuelve una lista de `steps` pronósticos (recursivo para ML).
"""
from __future__ import annotations
import logging
import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV, ElasticNet, LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

from .features import CORE, _design, make_exog_features

import structlog

logger = structlog.get_logger()

SEED = 42

import warnings
from statsmodels.tools.sm_exceptions import ConvergenceWarning

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    HAS_SM = True
except ImportError:
    HAS_SM = False

try:
    from lightgbm import LGBMRegressor
    HAS_LGBM = True
except ImportError:
    HAS_LGBM = False

try:
    from xgboost import XGBRegressor
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

ARIMA_GRID = [((0, 1, 0), "n"), ((0, 1, 0), "t"), ((1, 1, 0), "n"),
              ((0, 1, 1), "n"), ((1, 1, 1), "n")]
SARIMAX_ORDER, SARIMAX_SEASONAL = (1, 1, 0), (0, 0, 0, 0)
SARIMAX_EXOG = ["bolsa_mean", "embalse_pct", "oni", "trm_mean"]


def _make_model(name: str):
    if name == "Ridge":
        return RidgeCV(alphas=np.logspace(-1, 3, 17))
    if name == "ElasticNet":
        return ElasticNet(alpha=0.05, l1_ratio=0.5, max_iter=20000)
    if name == "RandomForest":
        return RandomForestRegressor(n_estimators=200, max_depth=4,
                                     min_samples_leaf=2, random_state=SEED, n_jobs=1)
    if name == "XGBoost":
        if not HAS_XGB:
            raise RuntimeError("xgboost no instalado")
        return XGBRegressor(n_estimators=150, max_depth=3, learning_rate=0.05,
                            subsample=0.8, colsample_bytree=0.8,
                            reg_alpha=1.0, reg_lambda=5.0,
                            random_state=SEED, verbosity=0)
    if name == "LightGBM":
        if not HAS_LGBM:
            raise RuntimeError("lightgbm no instalado")
        return LGBMRegressor(n_estimators=150, max_depth=3, num_leaves=7,
                             learning_rate=0.05, min_child_samples=2, min_data_in_bin=1,
                             reg_alpha=1.0, reg_lambda=5.0, subsample=0.8, subsample_freq=1,
                             colsample_bytree=0.8, random_state=SEED, verbose=-1)
    raise ValueError(f"Modelo no soportado: {name}")


def _predict_one(name: str, y_ext: pd.Series, exog: pd.DataFrame | None) -> float:
    """Predice el último punto (NaN) de y_ext con features hasta t-1. Devuelve nivel."""
    X, r = _design(y_ext, exog)
    y_last = float(y_ext.iloc[-2])
    Xh, rh = X.iloc[:-1], r.iloc[:-1]

    if name == "Drift3":
        rr = rh.dropna().tail(3)
        return y_last * float(np.exp(rr.mean() / 100)) if len(rr) else y_last

    if name == "Indexacion":
        cols = [c for c in ("ipc_var_l1", "ipp_var_l1") if c in X.columns]
        if not cols:
            return y_last
    else:
        cols = list(X.columns)

    ok = rh.notna() & Xh[CORE].notna().all(axis=1)
    if ok.sum() < 4 or X.iloc[[-1]][CORE].isna().any(axis=None):
        return y_last

    Xtr, rtr, Xte = Xh.loc[ok, cols], rh[ok], X.iloc[[-1]][cols]
    med = Xtr.median()
    keep = med.dropna().index
    if len(keep) == 0:
        return y_last
    Xtr, Xte = Xtr[keep].fillna(med[keep]), Xte[keep].fillna(med[keep])

    if name == "Indexacion":
        model = LinearRegression()
        model.fit(Xtr.values, rtr.values)
        return y_last * float(np.exp(model.predict(Xte.values)[0] / 100))

    sc = StandardScaler().fit(Xtr)
    model = _make_model(name)
    model.fit(sc.transform(Xtr), rtr.values)
    return y_last * float(np.exp(model.predict(sc.transform(Xte))[0] / 100))


def _predict_sm(name: str, y_hist: pd.Series, exog: pd.DataFrame | None, steps: int) -> list[float]:
    if not HAS_SM:
        raise RuntimeError("statsmodels no instalado")
    ly = np.log(y_hist.clip(lower=1e-6)).values

    if name == "ARIMA":
        best = None
        for order, trend in ARIMA_GRID:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", ConvergenceWarning)
                    res = ARIMA(ly, order=order, trend=trend).fit()
                if best is None or res.aic < best.aic:
                    best = res
            except Exception:
                continue
        if best is None:
            raise RuntimeError("ARIMA no convergió")
        return list(np.exp(best.forecast(steps)))

    if name == "SARIMAX":
        n = len(y_hist)
        idx_all = pd.date_range(y_hist.index[0], periods=n + steps, freq="MS")
        ex = make_exog_features(exog, idx_all)
        cols = [f"{c}_l1" for c in SARIMAX_EXOG if f"{c}_l1" in ex.columns]
        cols = [c for c in cols if ex[c].iloc[:n].notna().any()]
        if not cols:
            raise RuntimeError("SARIMAX sin exógenas disponibles")
        E = ex[cols].fillna(ex[cols].iloc[:n].median())
        E = (E - E.iloc[:n].mean()) / E.iloc[:n].std().replace(0, 1)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ConvergenceWarning)
            res = SARIMAX(ly, exog=E.iloc[:n].values, order=SARIMAX_ORDER,
                        seasonal_order=SARIMAX_SEASONAL,
                        enforce_stationarity=False,
                        enforce_invertibility=False).fit(disp=False)
            return list(np.exp(res.forecast(steps, exog=E.iloc[n:].values)))

    raise ValueError(name)


def predict_path(name: str, y_hist: pd.Series, exog: pd.DataFrame | None, steps: int = 1) -> list[float]:
    """
    Pronóstico de `steps` meses.
    - Naive/MA6/Rev50: directos.
    - ARIMA/SARIMAX: un tiro.
    - ML/Drift: recursivo (las exógenas se congelan en el último mes conocido).
    """
    y_hist = y_hist.astype(float).dropna()
    if y_hist.empty:
        raise ValueError("Serie vacía")

    if name == "Naive":
        return [float(y_hist.iloc[-1])] * steps

    if name in ("MA6", "Rev50"):
        ma, last = float(y_hist.tail(6).mean()), float(y_hist.iloc[-1])
        val = ma if name == "MA6" else last + 0.5 * (ma - last)
        return [val] * steps

    if name in ("ARIMA", "SARIMAX"):
        return _predict_sm(name, y_hist, exog, steps)

    y_ext, path = y_hist.copy(), []
    for _ in range(steps):
        nxt = y_ext.index[-1] + pd.offsets.MonthBegin(1)
        y_ext.loc[nxt] = np.nan
        yhat = _predict_one(name, y_ext, exog)
        y_ext.loc[nxt] = yhat
        path.append(float(yhat))
    return path