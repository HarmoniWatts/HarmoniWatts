# modules/forecast/exog.py
"""
Carga de exógenas mensuales usando la API REST de XM directamente (requests).
Sin pydataxm, sin aiohttp, sin anyio → seguro para asyncio.to_thread.

- MetricId exactos según POST https://servapibi.xm.com.co/lists {"MetricId": "ListadoMetricas"}
- embalse_pct = VoluUtilDiarEner / CapaUtilDiarEner (ambos Entity=Sistema, daily)
- Troceado por MaxDays según endpoint (hourly=30, daily=31)
- Caché en memoria + disco (Parquet, TTL 1 día)
- Logging de tiempos por métrica
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path

import pandas as pd
import requests

import structlog

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Configuración XM
# ---------------------------------------------------------------------------
XM_BASE = "https://servapibi.xm.com.co"
XM_TIMEOUT = 30                  # segundos por petición
XM_CACHE_TTL = 86400             # 1 día
XM_MAX_DIAS = {"hourly": 30, "daily": 31}   # restricción por endpoint

# MetricId exactos (ListadoMetricas). freq = endpoint: "hourly" | "daily"
XM_METRICAS = {
    "bolsa":        ("PrecBolsNaci",       "Sistema", "hourly"),
    "contr_reg":    ("PrecPromContRegu",   "Sistema", "hourly"),
    "contr_noreg":  ("PrecPromContNoRegu", "Sistema", "hourly"),
    "volu_util":    ("VoluUtilDiarEner",   "Sistema", "daily"),
    "capa_util":    ("CapaUtilDiarEner",   "Sistema", "daily"),
    "aportes":      ("AporEner",           "Sistema", "daily"),
    "rest_aliv":    ("RestAliv",           "Sistema", "hourly"),
    "rest_sinaliv": ("RestSinAliv",        "Sistema", "hourly"),
}

TRM_URL = "https://www.datos.gov.co/resource/ceyp-9c7c.json"
ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"


class ExogLoader:
    def __init__(
        self,
        hist_start: tuple[int, int],
        ipp_ipc_url: str | None = None,
        cache_dir: str | None = "cache",
    ):
        self.hist_start = pd.Timestamp(*hist_start, 1)
        self.ipp_ipc_url = ipp_ipc_url or os.getenv("IPP_IPC_URL")
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self._cache: pd.DataFrame | None = None

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def load(self, hoy: pd.Timestamp | None = None) -> pd.DataFrame:
        # 1. Caché en memoria
        if self._cache is not None:
            return self._cache

        # 2. Caché en disco (TTL)
        if self.cache_dir:
            path = self.cache_dir / "exog_mensual.parquet"
            if path.exists() and (time.time() - path.stat().st_mtime) < XM_CACHE_TTL:
                # logger.info("[exog] leyendo caché disco: %s", path)
                self._cache = pd.read_parquet(path)
                return self._cache

        # 3. Cargar de APIs
        t_total = time.perf_counter()
        hoy = (hoy or pd.Timestamp.today()).normalize()
        start = self.hist_start - pd.DateOffset(months=3)
        end = hoy - pd.Timedelta(days=1)
        # logger.info("[exog] cargando desde %s a %s", start.date(), end.date())

        cols: dict[str, pd.Series] = {}
        avisos: list[str] = []

        # --- XM ---
        for name, (metric, entity, freq) in XM_METRICAS.items():
            t0 = time.perf_counter()
            try:
                d = self._fetch_xm(metric, entity, freq, start, end)
                m = d.resample("MS")
                if name == "bolsa":
                    cols["bolsa_mean"] = m.mean()
                    cols["bolsa_max"] = m.max()
                    cols["bolsa_std"] = m.std()
                else:
                    cols[name] = m.mean()
                # logger.info("[exog] %-13s (%s/%s): %.1fs", name, metric, freq, time.perf_counter() - t0)
            except Exception as e:
                avisos.append(f"xm.{name}: {type(e).__name__}: {str(e)[:80]}")
                logger.warning("[exog] %-13s FALLÓ: %s: %s", name, type(e).__name__, str(e)[:80])

        # embalse_pct = volu_util / capa_util (evitar división por cero)
        if "volu_util" in cols and "capa_util" in cols:
            capa = cols.pop("capa_util")
            volu = cols.pop("volu_util")
            capa_safe = capa.replace(0, pd.NA)
            cols["embalse_pct"] = (volu / capa_safe).astype("float64")

        # --- TRM ---
        t0 = time.perf_counter()
        try:
            cols["trm_mean"] = self._fetch_trm(start, end).resample("MS").mean()
            # logger.info("[exog] trm_mean      : %.1fs", time.perf_counter() - t0)
        except Exception as e:
            avisos.append(f"trm: {type(e).__name__}: {str(e)[:80]}")
            logger.warning("[exog] trm_mean FALLÓ: %s: %s", type(e).__name__, str(e)[:80])

        # --- ONI ---
        t0 = time.perf_counter()
        try:
            cols["oni"] = self._fetch_oni()
            # logger.info("[exog] oni           : %.1fs", time.perf_counter() - t0)
        except Exception as e:
            avisos.append(f"oni: {type(e).__name__}: {str(e)[:80]}")
            logger.warning("[exog] oni FALLÓ: %s: %s", type(e).__name__, str(e)[:80])

        # --- IPC/IPP (opcional) ---
        t0 = time.perf_counter()
        try:
            for k, v in self._fetch_ipp_ipc().items():
                cols[k] = v
            if self.ipp_ipc_url:
                # logger.info("[exog] ipc/ipp       : %.1fs", time.perf_counter() - t0)
                pass
        except Exception as e:
            avisos.append(f"ipp/ipc: {type(e).__name__}: {str(e)[:80]}")
            logger.warning("[exog] ipc/ipp FALLÓ: %s: %s", type(e).__name__, str(e)[:80])

        for a in avisos:
            logger.warning("[exog] aviso: %s", a)

        if not cols:
            logger.error("[exog] sin columnas: todas las fuentes fallaron")
            self._cache = pd.DataFrame()
            return self._cache

        df = pd.DataFrame(cols).sort_index()
        df = df[df.index < hoy.replace(day=1)]      # descartar mes en curso (incompleto)

        # 4. Guardar caché disco
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            path = self.cache_dir / "exog_mensual.parquet"
            df.to_parquet(path)
            # logger.info("[exog] caché guardada: %s", path)

        # # logger.info("[exog] total %.1fs | shape=%s", time.perf_counter() - t_total, df.shape)
        self._cache = df
        return df

    # ------------------------------------------------------------------
    # XM (requests síncrono, troceado por MaxDays)
    # ------------------------------------------------------------------
    def _fetch_xm(self, metric: str, entity: str, freq: str,
                  start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
        max_dias = XM_MAX_DIAS.get(freq, 30)
        partes: list[pd.Series] = []
        cur = start
        n_llamadas = 0
        while cur <= end:
            ventana_fin = min(cur + pd.Timedelta(days=max_dias - 1), end)
            try:
                parte = self._fetch_xm_ventana(metric, entity, freq, cur, ventana_fin)
                if parte is not None and len(parte):
                    partes.append(parte)
            except requests.HTTPError as e:
                logger.warning(
                    "[exog] XM %s %s→%s HTTP %s",
                    metric, cur.date(), ventana_fin.date(), e.response.status_code,
                )
            n_llamadas += 1
            cur = ventana_fin + pd.Timedelta(days=1)

        if not partes:
            raise RuntimeError(f"XM sin datos ({metric}); {n_llamadas} llamadas")

        serie = pd.concat(partes).sort_index()
        # logger.debug("[exog] %s: %d llamadas, %d puntos", metric, n_llamadas, len(serie))
        return serie

    def _fetch_xm_ventana(self, metric: str, entity: str, freq: str,
                          start: pd.Timestamp, end: pd.Timestamp) -> pd.Series | None:
        url = f"{XM_BASE}/{freq}"
        body = {
            "MetricId": metric,
            "StartDate": start.strftime("%Y-%m-%d"),
            "EndDate": end.strftime("%Y-%m-%d"),
            "Entity": entity,
        }
        r = requests.post(url, json=body, timeout=XM_TIMEOUT)
        #logger.debug("[exog] XM status=%s body=%s", r.status_code, r.text[:500])
        r.raise_for_status()
        data = r.json()
        if not data or not isinstance(data, list):
            return None

        df = pd.DataFrame(data)
        if "Date" not in df.columns:
            return None
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"])

        # XM devuelve Values_HourXX para hourly; Value o columnas numéricas para daily
        hourly = [c for c in df.columns if c.startswith("Values_Hour")]
        if hourly:
            df["v"] = df[hourly].apply(pd.to_numeric, errors="coerce").mean(axis=1)
        elif "Value" in df.columns:
            df["v"] = pd.to_numeric(df["Value"], errors="coerce")
        else:
            num_cols = [
                c for c in df.columns
                if c != "Date" and pd.api.types.is_numeric_dtype(df[c])
            ]
            if not num_cols:
                return None
            df["v"] = df[num_cols].apply(pd.to_numeric, errors="coerce").mean(axis=1)

        return df.groupby("Date")["v"].mean()

    # ------------------------------------------------------------------
    # TRM (datos.gov.co)
    # ------------------------------------------------------------------
    @staticmethod
    def _fetch_trm(start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
        r = requests.get(
            TRM_URL, timeout=60,
            params={
                "$select": "valor,vigenciadesde",
                "$order": "vigenciadesde",
                "$limit": 50000,
                "$where": f"vigenciadesde >= '{start:%Y-%m-%d}T00:00:00.000'",
            },
        )
        r.raise_for_status()
        df = pd.DataFrame(r.json())
        df["vigenciadesde"] = pd.to_datetime(df["vigenciadesde"])
        s = df.set_index("vigenciadesde")["valor"].astype(float)
        s = s[~s.index.duplicated(keep="last")]
        return s.resample("D").ffill().loc[:end]

    # ------------------------------------------------------------------
    # ONI (NOAA)
    # ------------------------------------------------------------------
    @staticmethod
    def _fetch_oni() -> pd.Series:
        df = pd.read_csv(ONI_URL, sep=r"\s+")
        seas = {
            s: i + 1
            for i, s in enumerate(
                ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ",
                 "JJA", "JAS", "ASO", "SON", "OND", "NDJ"]
            )
        }
        df["date"] = pd.to_datetime(dict(year=df["YR"], month=df["SEAS"].map(seas), day=1))
        return df.set_index("date")["ANOM"].astype(float).rename("oni")

    # ------------------------------------------------------------------
    # IPC/IPP (opcional)
    # ------------------------------------------------------------------
    def _fetch_ipp_ipc(self) -> pd.DataFrame:
        if not self.ipp_ipc_url:
            return pd.DataFrame()
        df = (
            pd.read_csv(self.ipp_ipc_url, parse_dates=["fecha"])
            .set_index("fecha")
            .sort_index()
        )
        df.index = df.index.to_period("M").to_timestamp()
        return pd.DataFrame({
            "ipc_var": df["ipc"].pct_change() * 100,
            "ipp_var": df["ipp"].pct_change() * 100,
        })