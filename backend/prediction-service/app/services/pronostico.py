"""Pronóstico para el dashboard (HAR-25): predicción vs consumo real + próximos días + confianza.

Funciones puras: reciben la función `predecir(df) -> df` del modelo, así se prueban sin MLflow.

- Backtest: el modelo se ejecuta con la historia que tenía *antes* de los últimos `horas_pasadas`
  y su pronóstico se compara hora a hora con el consumo real de esas horas.
- Futuro: el modelo se ejecuta con la historia completa más reciente.
- Confianza: error porcentual ponderado (WAPE) de los totales de cada bloque de 24 h del backtest.
- Rango: percentil 80 del error absoluto por hora del día en el backtest.
"""
from __future__ import annotations

from typing import Callable, Optional

import numpy as np
import pandas as pd

Predecir = Callable[[pd.DataFrame], pd.DataFrame]

# Umbrales del nivel de confianza sobre el WAPE diario del backtest
UMBRAL_ALTA = 0.15
UMBRAL_MEDIA = 0.30
# Sin backtest no hay error medido: rango por defecto relativo al estimado
RANGO_RELATIVO_POR_DEFECTO = 0.30
# El backtest necesita al menos un día completo para ser representativo
MIN_HORAS_BACKTEST = 24


def nivel_confianza(wape_diario: Optional[float]) -> str:
    if wape_diario is None or not np.isfinite(wape_diario):
        return "bajo"
    if wape_diario <= UMBRAL_ALTA:
        return "alto"
    if wape_diario <= UMBRAL_MEDIA:
        return "medio"
    return "bajo"


def _wape(real: np.ndarray, estimado: np.ndarray) -> Optional[float]:
    total = float(np.sum(np.abs(real)))
    if total <= 0:
        return None
    return float(np.sum(np.abs(real - estimado)) / total)


def backtest(
    historia: pd.DataFrame, predecir: Predecir, min_historia: int, horas: int
) -> pd.DataFrame:
    """DataFrame [DATE_TIME, real_kwh, estimado_kwh] de las últimas `horas` horas reales,
    pronosticadas solo con la historia previa. Vacío si no hay historia suficiente."""
    disponibles = len(historia) - min_historia
    horas = min(horas, disponibles)
    if horas < MIN_HORAS_BACKTEST:
        return pd.DataFrame(columns=["DATE_TIME", "real_kwh", "estimado_kwh"])
    corte = len(historia) - horas
    previa = historia.iloc[corte - min_historia : corte]
    real = historia.iloc[corte:][["DATE_TIME", "kwh"]].rename(columns={"kwh": "real_kwh"})
    pred = predecir(previa[["METER_NO", "DATE_TIME", "kwh"]])
    pred = pred.rename(columns={"forecast_kwh": "estimado_kwh"})[["DATE_TIME", "estimado_kwh"]]
    return real.merge(pred, on="DATE_TIME", how="inner").reset_index(drop=True)


def metricas(bt: pd.DataFrame) -> dict:
    """Errores del backtest: WAPE horario y diario, y error por hora del día para el rango."""
    if bt.empty:
        return {"wape_horario": None, "wape_diario": None, "horas": 0, "dias": 0, "p80_por_hora": None}
    real = bt["real_kwh"].to_numpy(float)
    est = bt["estimado_kwh"].to_numpy(float)
    # "Días" = bloques de 24 h contados desde la última hora (no días del calendario: el backtest
    # empieza a cualquier hora y los días de los extremos quedarían incompletos)
    bloque = (np.arange(len(bt))[::-1] // 24)
    diario = bt.assign(dia=bloque)[bt.index >= len(bt) % 24]
    diario = diario.groupby("dia")[["real_kwh", "estimado_kwh"]].sum()
    abs_err = pd.Series(np.abs(real - est), index=bt["DATE_TIME"].dt.hour)
    p80 = abs_err.groupby(level=0).quantile(0.8).reindex(range(24))
    p80 = p80.fillna(float(abs_err.quantile(0.8)))
    return {
        "wape_horario": _wape(real, est),
        "wape_diario": _wape(diario["real_kwh"].to_numpy(), diario["estimado_kwh"].to_numpy()),
        "horas": int(len(bt)),
        "dias": int(len(diario)),
        "p80_por_hora": p80.to_numpy(float),
    }


def rango(fut: pd.DataFrame, p80_por_hora: Optional[np.ndarray]) -> pd.DataFrame:
    """Agrega [inferior_kwh, superior_kwh] al pronóstico futuro."""
    est = fut["estimado_kwh"].to_numpy(float)
    if p80_por_hora is None:
        margen = est * RANGO_RELATIVO_POR_DEFECTO
    else:
        margen = p80_por_hora[fut["DATE_TIME"].dt.hour.to_numpy()]
    return fut.assign(inferior_kwh=np.clip(est - margen, 0, None), superior_kwh=est + margen)


def pronosticar(
    historia: pd.DataFrame,
    predecir: Predecir,
    min_historia: int,
    horas_pasadas: int,
    horas_futuras: int,
) -> dict:
    """historia: [METER_NO, DATE_TIME, kwh] horario y ordenado, con >= min_historia filas."""
    bt = backtest(historia, predecir, min_historia, horas_pasadas)
    m = metricas(bt)

    fut = predecir(historia.iloc[-min_historia:][["METER_NO", "DATE_TIME", "kwh"]])
    fut = fut.rename(columns={"forecast_kwh": "estimado_kwh"})[["DATE_TIME", "estimado_kwh"]].head(horas_futuras)
    fut = rango(fut, m["p80_por_hora"])

    r3 = lambda v: round(float(v), 3)  # noqa: E731
    pct = lambda v: None if v is None else round(v * 100, 1)  # noqa: E731
    return {
        "historico": [
            {"timestamp": t.isoformat(), "real_kwh": r3(r), "estimado_kwh": r3(e)}
            for t, r, e in bt[["DATE_TIME", "real_kwh", "estimado_kwh"]].itertuples(index=False)
        ],
        "futuro": [
            {"timestamp": t.isoformat(), "estimado_kwh": r3(e), "inferior_kwh": r3(lo), "superior_kwh": r3(hi)}
            for t, e, lo, hi in fut[["DATE_TIME", "estimado_kwh", "inferior_kwh", "superior_kwh"]].itertuples(index=False)
        ],
        "confianza": {
            "nivel": nivel_confianza(m["wape_diario"]),
            "error_diario_pct": pct(m["wape_diario"]),
            "error_horario_pct": pct(m["wape_horario"]),
            "dias_evaluados": m["dias"],
            "horas_evaluadas": m["horas"],
            "metodo": "WAPE de los totales diarios en los días evaluados (alto ≤ 15 %, medio ≤ 30 %)",
        },
    }
