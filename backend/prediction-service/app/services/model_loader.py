import mlflow.pyfunc
from loguru import logger

from app.config import settings
from app.core.exceptions import ModelNotLoadedError


class ModelLoader:
    _model = None
    _version = None
    _uri = None
    
    @classmethod
    def load(cls, model_uri: str = None):
        """Carga el modelo desde MLflow Registry."""
        uri = model_uri or settings.MLFLOW_MODEL_URI
        logger.info(f"Cargando modelo desde {uri}")
        
        # Solo configura el servidor si el modelo viene del Registry (models:/)
        if uri.startswith("models:/") and getattr(settings, "MLFLOW_TRACKING_URI", None):
            mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
            
        cls._model = mlflow.pyfunc.load_model(uri)
        cls._uri = uri
        cls._version = uri.split("/")[-1]
        logger.info(f"Modelo cargado (versión {cls._version})")
        return cls._model
    
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