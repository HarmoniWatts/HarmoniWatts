import mlflow.pyfunc
from loguru import logger
from pathlib import Path

from app.config import settings
from app.core.exceptions import ModelNotLoadedError


class ModelLoader:
    _model = None
    _version = None
    _uri = None
    
    @classmethod
    def load(cls, model_uri: str = None):
        """Carga el modelo desde MLflow Registry."""
        uri = settings.MLFLOW_MODEL_URI
        es_local = cls._es_uri_local(uri)

        if es_local:
            # --- Modelo local: no tocar tracking URI ---
            path = Path(uri)
            if not path.exists():
                raise FileNotFoundError(
                    f"MLFLOW_MODEL_URI local no existe: {path.resolve()}"
                )
            logger.info("Cargando modelo LOCAL desde %s", path.resolve())
            cls._model = mlflow.pyfunc.load_model(str(path))
            cls._version = "local"
        else:
            # --- Modelo remoto: configurar tracking URI ---
            logger.info(
                "Cargando modelo REMOTO desde %s (tracking=%s)",
                uri, settings.MLFLOW_TRACKING_URI,
            )
            mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
            cls._model = mlflow.pyfunc.load_model(uri)
            cls._version = cls._extraer_version(uri)

        cls._uri = uri
        cls._es_local = es_local
        logger.info("Modelo cargado (uri=%s, version=%s, local=%s)",
                    cls._uri, cls._version, cls._es_local)

    @staticmethod
    def _es_uri_local(uri: str) -> bool:
        """
        Heurística:
          - Empieza por 'models:/', 'runs:/', 's3://', 'gs://', 'http' → remoto
          - Si es una ruta que existe en disco → local
          - Si no empieza por esquema conocido y no existe → asumir local (fallará con FileNotFoundError claro)
        """
        if uri.startswith(("models:/", "runs:/", "s3://", "gs://", "http://", "https://")):
            return False
        return True  # ruta local (existente o no; se valida al cargar)
    
    @classmethod
    def get_model(cls):
        if cls._model is None:
            raise ModelNotLoadedError("Modelo no cargado")
        return cls._model
    
    @classmethod
    def get_version(cls) -> str:
        return cls._version or "unknown"
    
    @classmethod
    def get_uri(cls) -> str:
        return cls._uri or settings.MLFLOW_MODEL_URI