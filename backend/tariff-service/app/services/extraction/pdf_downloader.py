import httpx
import re
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import date
from loguru import logger
from datetime import date, datetime, time

class PDFDownloader:
    """Descarga PDFs de tarifas desde la comercializadora"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, limit: int = 100):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self.limit = limit
        
        """Extrae mes y año desde títulos con formatos variados"""
        
        self.meses_es = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'setiembre': 9, 'octubre': 10,
            'noviembre': 11, 'diciembre': 12
        }
  
    def extraer_mes_anio(self, titulo: str) -> Optional[Tuple[int, int]]:
        """
        Extrae (mes, año) desde un título.
        
        Formatos soportados:
        - "Enero-2024"                                   → (1, 2024)
        - "Marzo-2025"                                   → (3, 2025)
        - "Marzo 21 y 22 de 2026 - Publicacion..."       → (3, 2026)
        - "Enero 22 de 2026 - Publicacion de Tarifas..."  → (1, 2026)
        - "Octubre 2025"                                 → (10, 2025)
        - "Diciembre de 2024"                            → (12, 2024)
        
        Retorna:
            (mes, año) o None si no se pudo extraer
        """
        if not titulo:
            return None
        
        titulo_lower = titulo.lower().strip()
        
        # Buscar mes en español (con o sin tilde)
        mes_encontrado = None
        for nombre, numero in self.meses_es.items():
            # Buscar la palabra completa del mes
            if re.search(rf'\b{nombre}\b', titulo_lower):
                mes_encontrado = numero
                break
        
        if not mes_encontrado:
            logger.warning(f"No se encontró mes en: {titulo}")
            return None
        
        # Buscar año (4 dígitos entre 2000 y 2099)
        match_anio = re.search(r'\b(20\d{2})\b', titulo)
        if not match_anio:
            logger.warning(f"No se encontró año en: {titulo}")
            return None
        
        anio_encontrado = int(match_anio.group(1))
        
        return (mes_encontrado, anio_encontrado)
    

    def extraer_dia(self, titulo: str) -> Optional[int]:
        """
        Extrae el día si está presente en el título.
        Ej: "Marzo 21 y 22 de 2026" → 21 (el primero)
            "Enero 22 de 2026" → 22
        """
        # Buscar "mes DD" o "mes DD de YYYY"
        match = re.search(r'\b(\d{1,2})\b', titulo)
        if match:
            dia = int(match.group(1))
            if 1 <= dia <= 31:
                return dia
        return None
    

    def extraer_fecha(self, titulo: str) -> Optional[date]:
        """
        Construye una fecha completa desde el título.
        Si el título tiene día, lo usa; si no, usa el día 1 del mes.
        """
        mes_anio = self.extraer_mes_anio(titulo)
        if not mes_anio:
            return None
        
        mes, anio = mes_anio
        dia = self.extraer_dia(titulo) or 1
        
        try:
            return date(anio, mes, dia)
        except ValueError:
            # Si el día no es válido (ej. 31 en febrero), usar día 1
            return date(anio, mes, 1)
    
    
    async def descargar_por_rango(
        self, 
        fecha_inicio: date, 
        fecha_fin: date,
        comercializadora_cod: str,
        filtro: list | str = ["Tarifas-", "Publicacion de Tarifas ETTC"]
    ) -> List[Path]:
        """Descarga PDFs en un rango de fechas"""
        print(f"Descargando PDFs de {comercializadora_cod} desde {fecha_inicio} hasta {fecha_fin} con filtro {filtro}")
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
        # params["where[createdAt][less_than_equal]"] = fecha_fin_ajustada.isoformat()

        # 3. Construimos dinámicamente los filtros [or] si es una lista/array
        if isinstance(filtro, list):
            for index, termino in enumerate(filtro):
                params[f"where[or][{index}][filename][contains]"] = termino
        else:
            # Mantiene la compatibilidad por si 'filtro' sigue siendo un solo string
            params["where[filename][contains]"] = filtro

        print(f"Parámetros de consulta: {params}")
        print(f"\nURL de la API: {self.base_url}/documents")
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
            
            print("\n")
            for doc in documentos:
                
                titulo = doc.get('title', '')
                fecha_doc = self.extraer_fecha(titulo)
                
                if fecha_doc is None:
                    logger.warning(f"Sin fecha reconocible, se omite: {titulo}")
                    continue
                
                if (fecha_inicio <= fecha_doc <= fecha_fin):
                    print(f"\nDescargando PDF: {doc['filename']} (creado en {doc['createdAt']})")
                    print(f"URL del PDF: {doc['url']}")
                    print(f"Descargando PDF dentro del rango: {fecha_inicio} a {fecha_fin}")
                    pdf_path = await self._descargar_pdf(client, doc['url'])
                    pdfs.append({ "path": pdf_path, "fecha": fecha_doc, "titulo": titulo })
                    logger.info(f"PDF descargado: {pdf_path}")
                continue
        
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