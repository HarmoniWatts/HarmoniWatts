from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from loguru import logger

from app.services.extraction.pdf_downloader import PDFDownloader
from app.services.extraction.pdf_parser import PDFParser
from app.services.extraction.data_validator import DataValidator
from app.services.extraction.tap_transformer import TAPTransformer
from app.repositories.postgres.tarifa_repository import TarifaRepository

from app.config import settings

class ExtractionService:
    """Orquesta el proceso completo de extracción"""
    
    def __init__(self, db: Session, pdf_downloader: PDFDownloader):
        self.db = db
        self.downloader = pdf_downloader(
            base_url=settings.COMERCIALIZADORA_API_URL
        )
        self.parser = PDFParser()
        self.validator = DataValidator()
        self.transformer = TAPTransformer()
        self.tarifa_repo = TarifaRepository(db)
    
    async def extraer_manual(
        self,
        comercializadora_id: int,
        fecha_inicio: date,
        fecha_fin: date
    ) -> dict:
        """Modo manual: extrae tarifas en un rango específico"""
        logger.info(f"Extracción manual: {fecha_inicio} a {fecha_fin}")
        
        # 1. Descargar PDFs
        pdfs = await self.downloader.descargar_por_rango(
            fecha_inicio, fecha_fin, comercializadora_id
        )
        
        if not pdfs:
            return {"estado": "sin_datos", "mensaje": "No se encontraron PDFs"}
        
        # 2. Procesar cada PDF
        resultado = await self._procesar_pdfs(pdfs, comercializadora_id)
        
        return resultado
    
    async def extraer_automatica(
        self,
        comercializadora_id: int
    ) -> dict:
        """Modo automático: extrae la última tarifa disponible"""
        logger.info(f"Extracción automática: comercializadora {comercializadora_id}")
        
        # 1. Descargar último PDF
        pdf = await self.downloader.descargar_ultimo(comercializadora_id)
        
        # 2. Procesar
        resultado = await self._procesar_pdfs([pdf], comercializadora_id)
        
        return resultado
    
    async def _procesar_pdfs(
        self, 
        pdfs: List, 
        comercializadora_id: int
    ) -> dict:
        """Procesa una lista de PDFs"""
        total_extraidas = 0
        total_insertadas = 0
        todos_errores = []
        
        for pdf_path in pdfs:
            try:
                # 1. Parsear PDF
                tarifas_raw = self.parser.parsear(pdf_path)
                total_extraidas += len(tarifas_raw)
                
                # 2. Validar y transformar
                for tarifa_raw in tarifas_raw:
                    metadata = self.parser._extraer_metadata_archivo(pdf_path)
                    
                    if not metadata.get('anio') or not metadata.get('mes'):
                        todos_errores.append(f"Sin metadata: {pdf_path.name}")
                        continue
                    
                    # Validar
                    es_valido, errores = self.validator.validar(
                        tarifa_raw, metadata['anio'], metadata['mes']
                    )
                    
                    if not es_valido:
                        todos_errores.extend(errores)
                        continue
                    
                    # Transformar a TAP
                    tarifa_tap = self.transformer.transformar(
                        tarifa_raw, comercializadora_id
                    )
                    
                    # 3. Insertar en PostgreSQL (si no existe)
                    insertada = self.tarifa_repo.upsert(tarifa_tap)
                    if insertada:
                        total_insertadas += 1
                
            except Exception as e:
                logger.error(f"Error procesando {pdf_path}: {e}")
                todos_errores.append(str(e))
        
        return {
            "estado": "completado",
            "tarifas_extraidas": total_extraidas,
            "tarifas_insertadas": total_insertadas,
            "errores": todos_errores
        }