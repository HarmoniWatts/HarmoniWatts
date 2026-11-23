from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "prediction-service"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # MongoDB
    MONGODB_HOST: str = "localhost"
    MONGODB_PORT: int = 27017
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "harmoniwatts"
    MONGODB_COLLECTION_PREDICCIONES: str = "predicciones_consumo"
    
    # Debug y logging
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # MLflow
    # MLFLOW_TRACKING_URI: str = "http://localhost:5000" # Si el servicio de MLflow en otro host, cambiar localhost por la IP 
    # MLFLOW_MODEL_URI: str = "models:/harmoniwatts-forecast@challenger" # Ruta si el servicio de MLflow está activo
    MLFLOW_MODEL_URI: str = "app/model" # Ruta local si el servicio de MLflow no está activo y se quiere usar un modelo descargado localmente
    
    
    # Consumption Service
    CONSUMPTION_SERVICE_URL: str = "http://localhost:8001"
    
    # HTTP Client
    HTTP_TIMEOUT_SEC: int = 30
    
    # Modelo
    HORIZONTE_HORAS: int = 168
    MIN_HISTORY_H: int = 504
    
    # Caché
    CACHE_TTL_SEC: int = 3600  # 1 hora
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()