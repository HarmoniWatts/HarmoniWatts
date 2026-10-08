# app/config.py

from pydantic_settings import BaseSettings
from typing import Optional
from enum import Enum


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "tariff-service"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8006
    
    # PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DATABASE: str = "harmoniwatts"
    
    # MongoDB
    MONGODB_USER: Optional[str] = None
    MONGODB_PASSWORD: Optional[str] = None
    MONGODB_HOST: str = "localhost"
    MONGODB_PORT: int = 27017
    MONGODB_DATABASE: str = "harmoniwatts_tariff"
    
    @property
    def MONGODB_URL(self) -> str:
        if self.MONGODB_USER and self.MONGODB_PASSWORD:
            return f"mongodb://{self.MONGODB_USER}:{self.MONGODB_PASSWORD}@{self.MONGODB_HOST}:{self.MONGODB_PORT}"
        return f"mongodb://{self.MONGODB_HOST}:{self.MONGODB_PORT}"
    
    # Redis (opcional - para Celery)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # External API de la comercializadora
    COMERCIALIZADORA_API_URL: str = "https://www.enertotalesp.com/api"
    COMERCIALIZADORA_API_KEY: Optional[str] = None
    COMERCIALIZADORA_API_TIMEOUT: int = 30
    
    # Auth
    INTERNAL_API_KEY: str = "dev-internal-key-123"
    
    # Sincronización
    SYNC_INTERVAL_SECONDS: int = 300
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Colecciones (para adaptarse a tus datos existentes)
    tariff_COLLECTION: str = "consumos_enriquecidos"
    USE_ALT_COLLECTION: bool = False
    HOUSEHOLD_ID_TYPE: str = "int"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # ← IGNORAR campos extra en lugar de rechazarlos
        case_sensitive = False


# Instanciar settings
settings = Settings()