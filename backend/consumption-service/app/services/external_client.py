import asyncio
from typing import Dict, Any, Optional, AsyncIterator
from datetime import date
from loguru import logger
# from tenacity import (
#     retry,
#     stop_after_attempt,
#     wait_exponential,
#     retry_if_exception_type,
# )

from app.config import settings
from app.core.http_client import HTTPClientManager


class InelcaClient:
    """
    Cliente para la API de INELCA (load profile).
    
    Endpoint: GET /apienert/enert/meter/load_profile
    Sin autenticación por ahora.
    """
    
    def __init__(self):
        self.base_url = settings.INELCA_BASE_URL
        self.per_page = settings.INELCA_PER_PAGE
        self.max_retries = settings.INELCA_MAX_RETRIES
        self.rate_limit_delay = settings.INELCA_RATE_LIMIT_DELAY_SEC
    
    # =====================================================
    # FETCH DE PÁGINA
    # =====================================================
    
    # @retry(
    #     stop=stop_after_attempt(3),
    #     wait=wait_exponential(multiplier=1, min=4, max=60),
    #     retry=retry_if_exception_type((
    #         httpx.TimeoutException,
    #         httpx.HTTPStatusError,
    #     )),
    # )
    async def _fetch_page(
        self,
        page: int,
        meter_no: str,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Consulta una página específica del load profile.
        
        Args:
            page: número de página (1-indexed)
            meter_no: número de medidor
            fecha_inicio: fecha inicial (opcional)
            fecha_fin: fecha final (opcional)
        """
        client = await HTTPClientManager.get_client()
        
        # Construir filtro
        filtro_partes = [f"METER_NO={meter_no}"]
        if fecha_inicio:
            filtro_partes.append(
                f"DATE_TIME>={fecha_inicio.strftime('%d/%m/%Y')} 00:00:00"
            )
        if fecha_fin:
            filtro_partes.append(
                f"DATE_TIME<={fecha_fin.strftime('%d/%m/%Y')} 23:59:59"
            )
        
        params = {
            "page": page,
            "perPage": self.per_page,
            "filter": "&".join(filtro_partes),
        }

        logger.debug(f"GET {self.base_url} params={params}")
        
        response = await client.get(self.base_url, params=params)
        response.raise_for_status()
        #logger.debug(f"response {response.json()}")
        return response.json()
    
    # =====================================================
    # ITERADOR DE PÁGINAS
    # =====================================================
    
    async def iter_meter_readings(
        self,
        meter_no: str,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        max_pages: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Itera sobre todas las lecturas de un medidor, página por página.
        
        Yields:
            Cada registro de `meters[]`
        """
        page = 1
        total_pages = 1
        total_registros = 0
        
        max_pages = max_pages or settings.INELCA_PER_PAGE
        
        while page <= total_pages and page <= max_pages:
            try:
                data = await self._fetch_page(
                    page=page,
                    meter_no=meter_no,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                )
            except Exception as e:
                logger.error(f"Error fetching page {page} for {meter_no}: {e}")
                break
            
            # Primera página: capturar metadata
            if page == 1:
                total_pages = data.get("totalPages", 1)
                total_registros = data.get("total", 0)
                logger.info(
                    f"Medidor {meter_no}: {total_registros} registros "
                    f"en {total_pages} páginas"
                )
            
            # Yield de cada lectura
            for lectura in data.get("meters", []):
                yield lectura
            
            page += 1
            
            # Rate limit
            if page <= total_pages:
                await asyncio.sleep(self.rate_limit_delay)
    
    # =====================================================
    # CONTEO RÁPIDO (solo metadata)
    # =====================================================
    
    async def contar_lecturas(
        self,
        meter_no: str,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Consulta solo la metadata (total, totalPages) sin descargar todo."""
        data = await self._fetch_page(
            page=1,
            meter_no=meter_no,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )
        return {
            "total": data.get("total", 0),
            "totalPages": data.get("totalPages", 0),
            "perPage": data.get("perPage", 0),
        }