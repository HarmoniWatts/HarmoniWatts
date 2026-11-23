import time
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from loguru import logger

from app.config import settings
from app.core.exceptions import InsufficientHistoryError, ModelNotLoadedError
from app.services.model_loader import ModelLoader
from app.services.consumption_client import ConsumptionClient
from app.repositories.prediction_repository import PredictionRepository
from app.services import pronostico as pron


class PredictionService:
    """
    Orquesta la predicción para un medidor.
    
    Flujo:
        1. Obtener historia del consumption-service.
        2. Invocar el modelo MLflow.
        3. Formatear respuesta.
        4. Persistir en MongoDB.
    """
    
    def __init__(self):
        self.consumption_client = ConsumptionClient()
        self.repo = PredictionRepository()
        
    
    async def predecir_consumo_contrato(
            self,
            no_contrato: int,
            cod_retail: str,
            id_cliente: Optional[int] = None,
            horizonte: int = settings.HORIZONTE_HORAS,
            persistir: bool = True,
        ) -> Dict[str, Any]:
            """
            Predice el consumo de un medidor en las próximas `horizonte` horas.
            
            Args:
                no_contrato: número de contrato
                cod_retail: código del comercializador
                id_cliente: id del cliente (opcional)
                horizonte: horas a predecir (default 168)
                persistir: si True, guarda en MongoDB
            
            Returns:
                Dict con la respuesta formateada según el contrato
            """
            inicio = time.time()
            
            HISTORY_BUFFER = 1.2   # 20% de margen

            horas_solicitadas = int(settings.MIN_HISTORY_H * HISTORY_BUFFER)  # 504 → 604
            
            # 1. Obtener historia
            meter_no, historia = await self.consumption_client.get_historia_horaria_contrato(
                no_contrato, cod_retail, horas=horas_solicitadas
            )
            
            # Recortar a las últimas MIN_HISTORY_H horas
            if len(historia) > settings.MIN_HISTORY_H:
                historia = historia.tail(settings.MIN_HISTORY_H).reset_index(drop=True)
                        
            # El modelo exige MIN_HISTORY_H horas: avisar con 404 en vez de un 500 del modelo
            if len(historia) < settings.MIN_HISTORY_H:
                raise InsufficientHistoryError(no_contrato, len(historia))
            
            # 2. Invocar el modelo
            model = ModelLoader.get_model()
            output_df = model.predict(historia[["METER_NO", "DATE_TIME", "kwh"]])
            
            # 3. Filtrar al horizonte solicitado
            output_df = output_df.head(horizonte)
            
            # 4. Formatear predicciones
            predicciones = [
                {
                    "timestamp": row.DATE_TIME.isoformat(),
                    "consumo_estimado_kwh": round(float(row.forecast_kwh), 3),
                }
                for row in output_df.itertuples()
            ]
            
            # 5. Metadatos
            metadatos = {
                "modelo_utilizado": "CentralFTForecaster",
                "version_modelo": ModelLoader.get_version(),
                "model_uri": ModelLoader.get_uri(),
                "duracion_ms": int((time.time() - inicio) * 1000),
            }
            
            # 6. Persistir
            doc_id = None
            if persistir:
                doc_id = await self.repo.guardar_prediccion(
                    no_contrato=no_contrato,
                    cod_retail=cod_retail,
                    id_cliente=id_cliente,
                    meter_no=meter_no,
                    horizonte_horas=horizonte,
                    predicciones=predicciones,
                    metadatos=metadatos,
                )
            
            return {
                "no_contrat": no_contrato,
                "cod_comercializadora": cod_retail,
                "id_cliente": id_cliente,
                "meter_no": meter_no,
                "generado_en": pd.Timestamp.utcnow().isoformat(),
                "horizonte_horas": len(predicciones),
                "modelo": {
                    "nombre": "CentralFTForecaster",
                    "version": ModelLoader.get_version(),
                },
                "predicciones": predicciones,
                "metadatos": metadatos,
                "id_prediccion": doc_id,
            }
    
    async def pronostico_contrato(
        self,
        no_contrato: str,
        cod_retail: str,
        dias_pasados: int = 7,
        dias_futuros: int = 7,
    ) -> Dict[str, Any]:
        """Predicción vs real de los últimos días (backtest), próximos días y confianza (HAR-25)."""
        inicio = time.time()
        min_h = settings.MIN_HISTORY_H
        horas_pasadas = dias_pasados * 24
        # Historia previa al backtest + horas evaluadas, con 15 % de margen por huecos
        horas_solicitadas = int((min_h + horas_pasadas) * 1.15)

        meter_no, historia = await self.consumption_client.get_historia_horaria_contrato(
            no_contrato, cod_retail, horas=horas_solicitadas
        )
        if len(historia) < min_h:
            raise InsufficientHistoryError(no_contrato, len(historia))

        model = ModelLoader.get_model()
        resultado = pron.pronosticar(
            historia.reset_index(drop=True),
            predecir=model.predict,
            min_historia=min_h,
            horas_pasadas=horas_pasadas,
            horas_futuras=dias_futuros * 24,
        )
        return {
            "no_contrato": str(no_contrato),
            "cod_comercializadora": cod_retail,
            "meter_no": meter_no,
            "generado_en": pd.Timestamp.utcnow().isoformat(),
            "ultima_lectura": historia["DATE_TIME"].iloc[-1].isoformat(),
            "modelo": {"nombre": "CentralFTForecaster", "version": ModelLoader.get_version()},
            **resultado,
            "metadatos": {"duracion_ms": int((time.time() - inicio) * 1000), "horas_historia": len(historia)},
        }

    async def predecir_medidor(
        self,
        meter_no: str,
        horizonte: int = settings.HORIZONTE_HORAS,
        persistir: bool = True,
    ) -> Dict[str, Any]:
        """
        Predice el consumo de un medidor en las próximas `horizonte` horas.
        
        Args:
            meter_no: número de medidor
            horizonte: horas a predecir (default 168)
            persistir: si True, guarda en MongoDB
        
        Returns:
            Dict con la respuesta formateada según el contrato
        """
        inicio = time.time()
        
        # 1. Obtener historia
        historia = await self.consumption_client.get_historia_horaria(
            meter_no, horas=settings.MIN_HISTORY_H
        )
        
        if len(historia) < settings.MIN_HISTORY_H:
            raise InsufficientHistoryError(meter_no, len(historia))
        
        # 2. Invocar el modelo
        model = ModelLoader.get_model()
        output_df = model.predict(historia[["METER_NO", "DATE_TIME", "kwh"]])
        
        # 3. Filtrar al horizonte solicitado
        output_df = output_df.head(horizonte)
        
        # 4. Formatear predicciones
        predicciones = [
            {
                "timestamp": row.DATE_TIME.isoformat(),
                "consumo_estimado_kwh": round(float(row.forecast_kwh), 3),
            }
            for row in output_df.itertuples()
        ]
        
        # 5. Metadatos
        metadatos = {
            "modelo_utilizado": "CentralFTForecaster",
            "version_modelo": ModelLoader.get_version(),
            "model_uri": ModelLoader.get_uri(),
            "duracion_ms": int((time.time() - inicio) * 1000),
        }
        
        # 6. Persistir
        doc_id = None
        if persistir:
            doc_id = await self.repo.guardar_prediccion(
                meter_no=meter_no,
                horizonte_horas=horizonte,
                predicciones=predicciones,
                metadatos=metadatos,
            )
        
        return {
            "meter_no": meter_no,
            "generado_en": pd.Timestamp.utcnow().isoformat(),
            "horizonte_horas": len(predicciones),
            "modelo": {
                "nombre": "CentralFTForecaster",
                "version": ModelLoader.get_version(),
            },
            "predicciones": predicciones,
            "metadatos": metadatos,
            "id_prediccion": doc_id,
        }
    
    async def predecir_batch(
        self,
        meters: List[str],
        horizonte: int = settings.HORIZONTE_HORAS,
        persistir: bool = True,
    ) -> Dict[str, Any]:
        """
        Predice múltiples medidores en una sola llamada.
        """
        resultados = []
        exitosos = 0
        fallidos = 0
        omitidos = []
        
        for meter_no in meters:
            try:
                resultado = await self.predecir_medidor(
                    meter_no, horizonte, persistir
                )
                resultados.append({
                    "meter_no": meter_no,
                    "estado": "ok",
                    **resultado,
                })
                exitosos += 1
            except InsufficientHistoryError as e:
                omitidos.append({"meter_no": meter_no, "motivo": str(e)})
            except Exception as e:
                logger.error(f"Error prediciendo {meter_no}: {e}")
                resultados.append({
                    "meter_no": meter_no,
                    "estado": "error",
                    "mensaje": str(e),
                })
                fallidos += 1
        
        return {
            "total_medidores": len(meters),
            "exitosos": exitosos,
            "fallidos": fallidos,
            "omitidos": omitidos,
            "resultados": resultados,
        }