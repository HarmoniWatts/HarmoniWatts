"""Variables compartidas entre entrenamiento y servicio (única fuente de verdad)."""
import numpy as np
import pandas as pd
import holidays as pyholidays

H = 168                                   # horizonte (h)
LAGS = (168, 336, 504)                    # rezagos ≥ horizonte: disponibles en todo el horizonte
MIN_HISTORY_H = max(LAGS)
CAL2 = ["hour_sin", "hour_cos", "dow_sin", "dow_cos", "is_weekend", "is_holiday"]


def holiday_set(years):
    return set(pyholidays.country_holidays("CO", years=list(years)).keys())


def calendar_frame(idx, hol):
    d = pd.DataFrame(index=idx)
    d["hour"] = idx.hour
    d["dow"] = idx.dayofweek
    d["is_weekend"] = (idx.dayofweek >= 5).astype(int)
    d["is_holiday"] = pd.Series(idx.date, index=idx).isin(hol).astype(int).values
    d["dayoff"] = ((d["is_weekend"] == 1) | (d["is_holiday"] == 1)).astype(int)
    d["hod_dayoff"] = d["hour"] + 24 * d["dayoff"]
    d["hour_sin"] = np.sin(2 * np.pi * d["hour"] / 24)
    d["hour_cos"] = np.cos(2 * np.pi * d["hour"] / 24)
    d["dow_sin"] = np.sin(2 * np.pi * d["dow"] / 7)
    d["dow_cos"] = np.cos(2 * np.pi * d["dow"] / 7)
    return d


def mlp_features(Yn_, cal):
    """Tensor (T, N, F): rezagos >=168 h del consumo normalizado + calendario."""
    lags = [Yn_.shift(l).values for l in LAGS]
    lag_mean = (lags[0] + lags[1] + lags[2]) / 3
    wk = Yn_.shift(168).rolling(168).mean().values
    calb = np.repeat(cal[CAL2].values[:, None, :], Yn_.shape[1], axis=1)
    return np.concatenate([np.stack(lags, -1), lag_mean[..., None], wk[..., None], calb], -1).astype("float32")


def prepare_inputs(df, scale_n, horizon=H):
    """df: DataFrame [METER_NO, DATE_TIME, kwh] horario. Pronostica las `horizon` horas siguientes a su ultima hora.
    scale_n: dict medidor -> media de entrenamiento (medidores nuevos: se usa la media de su historia)."""
    wide = df.pivot_table(index="DATE_TIME", columns="METER_NO", values="kwh", aggfunc="mean")
    wide = wide.reindex(pd.date_range(wide.index.min(), wide.index.max(), freq="h"))
    wide = wide.interpolate(limit=6, limit_area="inside")
    if len(wide) < MIN_HISTORY_H:
        raise ValueError(f"Se requieren al menos {MIN_HISTORY_H} h de historia horaria; llegaron {len(wide)}")
    wide = wide.iloc[-MIN_HISTORY_H:]
    ok = wide.notna().all()
    skipped = [str(c) for c in wide.columns[~ok]]            # medidores con huecos en la ventana: no se pronostican
    wide = wide.loc[:, ok]
    scale = np.array([scale_n.get(str(m), np.nan) for m in wide.columns], float)
    scale = np.clip(np.where(np.isfinite(scale), scale, wide.mean().values), 1e-6, None)
    origin = wide.index[-1] + pd.Timedelta(hours=1)
    fidx = pd.date_range(origin, periods=horizon, freq="h")
    allidx = wide.index.append(fidx)
    cal = calendar_frame(allidx, holiday_set(range(allidx.min().year, allidx.max().year + 1)))
    X = mlp_features((wide / scale).reindex(allidx), cal)[-horizon:]
    assert np.isfinite(X).all(), "Variables no finitas: historia insuficiente o con huecos"
    return dict(meters=[str(m) for m in wide.columns], fidx=fidx, X=X, scale=scale, history=wide, skipped=skipped)
