import httpx
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd
from loguru import logger

from app.config import settings
from app.core.http_client import HTTPClientManager
from app.core.exceptions import ConsumptionServiceError


class ConsumptionClient:
    """Cliente para consultar el consumo histórico del consumption-service."""
    
    def __init__(self):
        self.base_url = settings.CONSUMPTION_SERVICE_URL.rstrip("/")
        
    
    async def get_historia_horaria_contrato(
        self,
        no_contrato: int,
        cod_retail: str,
        horas: int = 504,
    ) -> pd.DataFrame:
        """
        Obtiene la historia horaria de un medidor según el número de contrato-comercializador.

        Backend devuelve: {"data": [{"timestamp": "...", "kwh": 0.019}, ...]}

        Returns:
            DataFrame [METER_NO, DATE_TIME, kwh] ordenado cronológicamente.
        """
        client = await HTTPClientManager.get_client()
        logger.info(f"url consumos: {self.base_url}/api/v1/consumption/series/raws/{no_contrato}/{cod_retail}")
        try:
            response = await client.get(
                f"{self.base_url}/api/v1/consumption/series/raws/{no_contrato}/{cod_retail}",
                params={"hours": horas},
                timeout=30,
            )

            if response.status_code == 404:
                logger.warning(
                    "Sin historia para número de contrato %s - comercializador %s",
                    no_contrato, cod_retail,
                )
                return "", pd.DataFrame(columns=["METER_NO", "DATE_TIME", "kwh"])

            response.raise_for_status()
            payload = response.json()

            # --- Validación defensiva ---
            if not isinstance(payload, dict) or "data" not in payload:
                raise ValueError(
                    f"Respuesta inesperada: {type(payload)}; "
                    f"claves={list(payload) if isinstance(payload, dict) else 'N/A'}"
                )
            
            serie_medidor = payload["serie_medidor"]
            registros = payload["data"]
            if not registros:
                logger.warning(
                    "Historia vacía para contrato %s - retail %s", no_contrato, cod_retail
                )
                return serie_medidor, pd.DataFrame(columns=["METER_NO", "DATE_TIME", "kwh"])

            # --- Transformación ---
            df = pd.DataFrame(registros)

            # Verificar columnas
            faltantes = {"timestamp", "kwh"} - set(df.columns)
            if faltantes:
                raise ValueError(f"Faltan columnas en la respuesta: {faltantes}")

            df = df.rename(columns={"timestamp": "DATE_TIME"})
            
            df["METER_NO"] =  df["meter_no"]
            
            # --- DATE_TIME: UTC (Z) → Bogotá → naive ---
            df["DATE_TIME"] = (
                pd.to_datetime(df["DATE_TIME"], utc=True, errors="coerce")
                .dt.tz_convert("America/Bogota")
                .dt.tz_localize(None)          # ← clave: el modelo exige naive
            )
        
            df["kwh"] = pd.to_numeric(df["kwh"], errors="coerce")

            # Descartar filas con timestamp inválido
            n_invalidos = df["DATE_TIME"].isna().sum()
            if n_invalidos:
                logger.warning(
                    "Contrato %s: %d filas con timestamp inválido descartadas",
                    no_contrato, n_invalidos,
                )
                df = df.dropna(subset=["DATE_TIME"])

            # Orden cronológico ascendente
            df = df.sort_values("DATE_TIME").reset_index(drop=True)

            # Aviso si hay huecos no horarios
            if len(df) > 1:
                diffs = df["DATE_TIME"].diff().dropna()
                n_huecos = int((diffs != pd.Timedelta(hours=1)).sum())
                if n_huecos:
                    logger.warning(
                        "Contrato %s: %d huecos no horarios en la historia",
                        no_contrato, n_huecos,
                    )

            return serie_medidor, df[["METER_NO", "DATE_TIME", "kwh"]]
            
        except httpx.HTTPError as e:
            logger.error(f"Error consultando consumption-service: {e}")
            raise ConsumptionServiceError(str(e)) from e
    
    async def get_historia_horaria(
        self,
        meter_no: str,
        horas: int = 504,
    ) -> pd.DataFrame:
        """
        Obtiene la historia horaria de un medidor.
        
        Returns:
            DataFrame [METER_NO, DATE_TIME, kwh]
        """
        client = await HTTPClientManager.get_client()
        
        try:
            response = await client.get(
                f"{self.base_url}/api/v1/consumption/series/hourly/{meter_no}",
                params={"hours": horas},
                timeout=30,
            )
            
            if response.status_code == 404:
                logger.warning(f"Sin historia para medidor {meter_no}")
                return pd.DataFrame(columns=["METER_NO", "DATE_TIME", "kwh"])
            
            response.raise_for_status()
            data = response.json()
            
            # Transformar a DataFrame
            df = pd.DataFrame({
                "METER_NO": meter_no,
                "DATE_TIME": pd.to_datetime(data["labels"]),
                "kwh": data["values_kwh"],
            })
            
            return df
            
        except httpx.HTTPError as e:
            logger.error(f"Error consultando consumption-service: {e}")
            raise ConsumptionServiceError(str(e)) from e