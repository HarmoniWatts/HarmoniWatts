# app/config.py

from pydantic_settings import BaseSettings
from typing import Optional
from enum import Enum
from pathlib import Path


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "consumption-service"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8003
    
    # MongoDB
    MONGODB_USER: Optional[str] = None
    MONGODB_PASSWORD: Optional[str] = None
    MONGODB_HOST: str = "localhost"
    MONGODB_PORT: int = 27017
    MONGODB_DATABASE: str = "harmoniwatts"
    MONGODB_COLLECTION_CONSUMOS: str = "consumos_enriquecidos"
    
    @property
    def MONGODB_URL(self) -> str:
        if self.MONGODB_USER and self.MONGODB_PASSWORD:
            return f"mongodb://{self.MONGODB_USER}:{self.MONGODB_PASSWORD}@{self.MONGODB_HOST}:{self.MONGODB_PORT}"
        return f"mongodb://{self.MONGODB_HOST}:{self.MONGODB_PORT}"
    
    
     # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    
    # Redis (opcional - para Celery)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # External API
    EXTERNAL_API_BASE_URL: str = "https://api.smartmeter.com.co"
    EXTERNAL_API_KEY: Optional[str] = None
    EXTERNAL_API_TIMEOUT: int = 30
    
    # API INELCA
    INELCA_BASE_URL: str = "https://www.ami.inelca.app/apienert/enert/meter/load_profile"
    INELCA_PER_PAGE: int = 2000
    INELCA_TIMEOUT_SEC: int = 60
    INELCA_RATE_LIMIT_DELAY_SEC: float = 0.5
    INELCA_MAX_RETRIES: int = 3
    # El servidor de INELCA no envía el certificado intermedio de su cadena
    # (Go Daddy Secure Certificate Authority - G2). Windows lo descarga solo,
    # pero en Linux/Docker la verificación TLS falla sin él.
    EXTRA_CA_FILE: Optional[str] = str(Path(__file__).resolve().parent.parent / "certs" / "gdig2.pem")
    
    
    # Tariff Service
    TARIFF_SERVICE_URL: str = "http://127.0.0.1:8006"   # Ej: "http://localhost:8006"
    
    # User Service (futuro)
    USER_SERVICE_URL: str = ""     # Ej: "http://localhost:8002"
    
    # Auth
    INTERNAL_API_KEY: str = "dev-internal-key-123"
    
    # Sincronización
    SYNC_INTERVAL_SECONDS: int = 300
    SYNC_BATCH_SIZE: int = 1000
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Colecciones (para adaptarse a tus datos existentes)
    CONSUMPTION_COLLECTION: str = "consumos_enriquecidos"
    USE_ALT_COLLECTION: bool = False
    CONTRAT_ID_TYPE: str = "int"
    # Día civil y horas del gráfico / agregaciones (debe coincidir con insights-service)
    DEFAULT_TIMEZONE: str = "America/Bogota"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # ← IGNORAR campos extra en lugar de rechazarlos
        case_sensitive = False


# Instanciar settings
settings = Settings()