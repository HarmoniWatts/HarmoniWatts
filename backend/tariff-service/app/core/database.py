from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import QueuePool
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Base declarativa para modelos ORM
Base = declarative_base()


class PostgreSQLManager:
    """
    Gestor de conexión a PostgreSQL.
    Sigue el mismo patrón que MongoDBManager para consistencia.
    """
    engine = None
    SessionLocal = None
    
    @classmethod
    def connect(cls):
        """Establece la conexión a PostgreSQL"""
        logger.info(
            "connecting_to_postgresql host=%s database=%s user=%s",
            settings.POSTGRES_HOST,
            settings.POSTGRES_DATABASE,
            settings.POSTGRES_USER,
        )
        
        # Construir URL de conexión
        database_url = (
            f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
            f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DATABASE}"
        )
        
        # Crear engine con pool de conexiones
        cls.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=10,              # Conexiones persistentes
            max_overflow=20,           # Conexiones adicionales bajo demanda
            pool_pre_ping=True,        # Verificar conexión antes de usar
            pool_recycle=3600,         # Reciclar conexiones cada 1 hora
            echo=settings.SQL_ECHO,    # Log de SQL (solo en desarrollo)
            future=True                # SQLAlchemy 2.0 style
        )
        
        # Configurar eventos para logging
        cls._setup_events()
        
        # Crear sessionmaker
        cls.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=cls.engine,
            expire_on_commit=False     # Evita queries adicionales después del commit
        )
        
        logger.info("postgresql_connected")
    
    @classmethod
    def _setup_events(cls):
        """Configura eventos de SQLAlchemy para logging y debugging"""
        
        @event.listens_for(cls.engine, "connect")
        def on_connect(dbapi_conn, connection_record):
            """Se ejecuta al establecer una nueva conexión"""
            logger.debug("new_connection_established")
            # Configurar timezone de sesión
            with dbapi_conn.cursor() as cursor:
                cursor.execute("SET timezone = 'America/Bogota'")
        
        @event.listens_for(cls.engine, "checkout")
        def on_checkout(dbapi_conn, connection_record, connection_proxy):
            """Se ejecuta al tomar una conexión del pool"""
            logger.debug("connection_checked_out")
        
        @event.listens_for(cls.engine, "checkin")
        def on_checkin(dbapi_conn, connection_record):
            """Se ejecuta al devolver una conexión al pool"""
            logger.debug("connection_checked_in")
    
    @classmethod
    def create_tables(cls):
        """Crea todas las tablas definidas en los modelos"""
        try:
            Base.metadata.create_all(bind=cls.engine)
            logger.info("tables_created")
        except Exception as e:
            logger.error("error_creating_tables: %s", e)
            raise
    
    @classmethod
    def drop_tables(cls):
        """Elimina todas las tablas (¡cuidado en producción!)"""
        try:
            Base.metadata.drop_all(bind=cls.engine)
            logger.warning("tables_dropped")
        except Exception as e:
            logger.error("error_dropping_tables: %s", e)
            raise
    
    @classmethod
    def health_check(cls) -> bool:
        """Verifica que la conexión a PostgreSQL esté activa"""
        try:
            with cls.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error("postgresql_health_check_failed: %s", e)
            return False
    
    @classmethod
    def close(cls):
        """Cierra el pool de conexiones"""
        if cls.engine:
            cls.engine.dispose()
            logger.info("postgresql_disconnected")


# =====================================================
# DEPENDENCIAS DE FASTAPI
# =====================================================

def get_db() -> Generator[Session, None, None]:
    """
    Dependencia de FastAPI para obtener una sesión de BD.
    Se cierra automáticamente al terminar la petición.
    
    Uso:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = PostgreSQLManager.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session() -> Session:
    """
    Obtiene una sesión de BD sin ser dependencia de FastAPI.
    Útil para scripts, tareas Celery o jobs programados.
    
    Uso:
        with get_session() as db:
            ...
    """
    return PostgreSQLManager.SessionLocal()


# =====================================================
# EVENTOS DE CICLO DE VIDA (FastAPI lifespan)
# =====================================================

from contextlib import asynccontextmanager
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Maneja el ciclo de vida de la aplicación.
    Conecta a PostgreSQL al iniciar y cierra al terminar.
    """
    # Startup
    logger.info("application_starting")
    PostgreSQLManager.connect()
    
    # Verificar conexión
    if not PostgreSQLManager.health_check():
        logger.error("postgresql_connection_failed")
        raise RuntimeError("No se pudo conectar a PostgreSQL")
    
    # Opcional: crear tablas automáticamente en desarrollo
    if settings.ENVIRONMENT == "development":
        PostgreSQLManager.create_tables()
    
    yield
    
    # Shutdown
    logger.info("application_shutting_down")
    PostgreSQLManager.close()