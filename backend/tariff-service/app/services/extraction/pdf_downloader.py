import httpx
from pathlib import Path
from typing import List, Optional
from datetime import date
from loguru import logger
from datetime import date, datetime, time

class PDFDownloader:
    """Descarga PDFs de tarifas desde la comercializadora"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    
    async def descargar_por_rango(
        self, 
        fecha_inicio: date, 
        fecha_fin: date,
        filtro: list | str = ["Tarifas-", "Publicacion de Tarifas ETTC"]
    ) -> List[Path]:
        """Descarga PDFs en un rango de fechas"""
        pdfs = []
        
        page = 1

        # 1. Inicializamos los parámetros base
        params = {
            "sort": "-createdAt",
            "mimeType": "application/pdf",
            "limit": self.limit,
            "page": page,
        }

        # 2. Filtro por rango de fechas (createdAt)
        #    Greater than or equal a fecha_inicio
        params["where[createdAt][greater_than_equal]"] = fecha_inicio.isoformat()

        #    Less than or equal a fecha_fin (incluir todo el día final)
        #    Se ajusta fecha_fin al final del día para incluir documentos de ese día
        fecha_fin_ajustada = datetime.combine(fecha_fin, time.max)
        params["where[createdAt][less_than_equal]"] = fecha_fin_ajustada.isoformat()

        # 3. Construimos dinámicamente los filtros [or] si es una lista/array
        if isinstance(filtro, list):
            for index, termino in enumerate(filtro):
                params[f"where[or][{index}][filename][contains]"] = termino
        else:
            # Mantiene la compatibilidad por si 'filtro' sigue siendo un solo string
            params["where[filename][contains]"] = filtro

        
        async with httpx.AsyncClient() as client:
            # Consultar qué PDFs están disponibles en el rango
            response = await client.get(
                f"{self.base_url}/documents",
                params=params,
                headers=self.headers
            )
            response.raise_for_status()
            
            data = response.json()
            documentos = data.get("docs")
            
            for doc in documentos:
                pdf_path = await self._descargar_pdf(client, doc['url'])
                pdfs.append(pdf_path)
                logger.info(f"PDF descargado: {pdf_path}")
        
        return pdfs
    
    async def descargar_ultimo(self, filtro: list | str = ["Tarifas-", "Publicacion de Tarifas ETTC"]) -> Path:
        """Descarga el último PDF publicado"""
        
        page = 1
        
        # 1. Inicializamos los parámetros base
        params = {
            "sort": "-createdAt",
            "mimeType": "application/pdf",
            "limit": 1,
            "page": page,
        }


        # 2. Construimos dinámicamente los filtros [or] si es una lista/array
        if isinstance(filtro, list):
            for index, termino in enumerate(filtro):
                params[f"where[or][{index}][filename][contains]"] = termino
        else:
            # Mantiene la compatibilidad por si 'filtro' sigue siendo un solo string
            params["where[filename][contains]"] = filtro
                    
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/documents",
                params=params,
                headers=self.headers
            )
            response.raise_for_status()
            
            data = response.json()
            doc = data.get("docs")
            return await self._descargar_pdf(client, doc['url'])
    
    async def _descargar_pdf(self, client: httpx.AsyncClient, url: str) -> Path:
        """Descarga un PDF individual"""
        response = await client.get(url, headers=self.headers)
        response.raise_for_status()
        
        # Guardar en directorio temporal
        pdf_dir = Path("/tmp/tariffs")
        pdf_dir.mkdir(parents=True, exist_ok=True)
        
        filename = url.split('/')[-1]
        pdf_path = pdf_dir / filename
        
        pdf_path.write_bytes(response.content)
        return pdf_path