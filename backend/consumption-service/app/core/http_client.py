import os
import ssl
import truststore
import httpx
from loguru import logger
from app.config import settings


class HTTPClientManager:
    """Gestor del cliente HTTP compartido para llamadas a APIs externas."""
    
    client: httpx.AsyncClient = None
    
    @classmethod
    async def connect(cls) -> httpx.AsyncClient:
        """
        Inicializa el cliente HTTP (idempotente).
        Si ya existe, lo devuelve sin recrearlo.
        """
        if cls.client is None:
            
            # Usar el almacén de certificados del sistema operativo
            ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            # Intermedios que algunos servidores (INELCA) no envían en su cadena
            if settings.EXTRA_CA_FILE and os.path.isfile(settings.EXTRA_CA_FILE):
                ctx.load_verify_locations(cafile=settings.EXTRA_CA_FILE)

            cls.client = httpx.AsyncClient(
                timeout=httpx.Timeout(settings.INELCA_TIMEOUT_SEC),
                limits=httpx.Limits(
                    max_connections=20,
                    max_keepalive_connections=10,
                ),
                headers={"User-Agent": "HarmoniWatts/1.0"},
                verify=ctx  # Pasar el contexto SSL
            )
            logger.info("HTTPClientManager conectado")
        return cls.client
    
    @classmethod
    async def close(cls):
        """Cierra el cliente y limpia la referencia."""
        if cls.client:
            await cls.client.aclose()
            cls.client = None
            logger.info("HTTPClientManager cerrado")
    
    @classmethod
    async def get_client(cls) -> httpx.AsyncClient:
        """
        Obtiene el cliente HTTP.
        Si no está inicializado, lo inicializa automáticamente.
        
        Uso:
            client = await HTTPClientManager.get_client()
        """
        if cls.client is None:
            await cls.connect()
        return cls.client