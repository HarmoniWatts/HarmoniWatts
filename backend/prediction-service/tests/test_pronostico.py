"""Pruebas de app/services/pronostico.py con un "modelo" falso (repite la semana anterior)."""
import numpy as np
import pandas as pd

from app.services import pronostico as pron

MIN_H = 504


def historia(horas: int, inicio="2026-10-01", ruido=0.0, seed=0) -> pd.DataFrame:
    idx = pd.date_range(inicio, periods=horas, freq="h")
    base = 0.2 + 0.3 * (idx.hour >= 18)  # más consumo de 18 a 23
    rng = np.random.default_rng(seed)
    kwh = base * (1 + ruido * rng.standard_normal(horas))
    return pd.DataFrame({"METER_NO": "M1", "DATE_TIME": idx, "kwh": np.clip(kwh, 0, None)})


def naive_semanal(df: pd.DataFrame) -> pd.DataFrame:
    """Pronostica las 168 h siguientes repitiendo las últimas 168."""
    ultimas = df.tail(168)
    fidx = pd.date_range(df["DATE_TIME"].iloc[-1] + pd.Timedelta(hours=1), periods=168, freq="h")
    return pd.DataFrame({"METER_NO": "M1", "DATE_TIME": fidx, "forecast_kwh": ultimas["kwh"].to_numpy()})


def test_patron_perfecto_da_confianza_alta_y_rango_cero():
    r = pron.pronosticar(historia(MIN_H + 168), naive_semanal, MIN_H, 168, 168)
    assert len(r["historico"]) == 168
    assert len(r["futuro"]) == 168
    assert r["confianza"]["nivel"] == "alto"
    assert r["confianza"]["error_diario_pct"] == 0.0
    assert r["confianza"]["dias_evaluados"] == 7
    f = r["futuro"][0]
    assert f["inferior_kwh"] == f["estimado_kwh"] == f["superior_kwh"]


def test_historico_compara_con_el_real_de_esas_horas():
    h = historia(MIN_H + 48)
    r = pron.pronosticar(h, naive_semanal, MIN_H, 48, 24)
    assert [p["timestamp"] for p in r["historico"]] == [t.isoformat() for t in h["DATE_TIME"].iloc[-48:]]
    assert r["historico"][-1]["real_kwh"] == round(float(h["kwh"].iloc[-1]), 3)
    # El futuro empieza justo después de la última lectura
    assert r["futuro"][0]["timestamp"] == (h["DATE_TIME"].iloc[-1] + pd.Timedelta(hours=1)).isoformat()


def test_ruido_baja_la_confianza_y_abre_el_rango():
    r = pron.pronosticar(historia(MIN_H + 168, ruido=0.8, seed=1), naive_semanal, MIN_H, 168, 24)
    assert r["confianza"]["nivel"] in ("medio", "bajo")
    assert r["confianza"]["error_horario_pct"] > r["confianza"]["error_diario_pct"]
    f = r["futuro"][0]
    assert f["inferior_kwh"] <= f["estimado_kwh"] < f["superior_kwh"]


def test_sin_historia_para_backtest_usa_rango_por_defecto_y_confianza_baja():
    r = pron.pronosticar(historia(MIN_H + 10), naive_semanal, MIN_H, 168, 24)
    assert r["historico"] == []
    assert r["confianza"]["nivel"] == "bajo"
    assert r["confianza"]["error_diario_pct"] is None
    f = r["futuro"][0]
    assert abs(f["superior_kwh"] - f["estimado_kwh"] * 1.3) < 1e-3


def test_niveles():
    assert pron.nivel_confianza(0.10) == "alto"
    assert pron.nivel_confianza(0.25) == "medio"
    assert pron.nivel_confianza(0.50) == "bajo"
    assert pron.nivel_confianza(None) == "bajo"
