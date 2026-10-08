from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.config import settings
from app.services.extraction.pdf_downloader import PDFDownloader
from app.repositories.postgres.tarifa_repository import TarifaRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_pdf_downloader() -> PDFDownloader:
    """Dependencia de API: descargador de PDFs configurado"""
    return PDFDownloader(
        base_url=settings.COMERCIALIZADORA_API_URL,
        limit=settings.PDF_DOWNLOAD_LIMIT or 100
    )


def get_tarifa_repository(db: Session = Depends(get_db)) -> TarifaRepository:
    """Dependencia de API: repositorio de tarifas"""
    return TarifaRepository(db)


def get_current_cliente(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Dependencia de API: cliente autenticado"""
    # ... validar token, retornar cliente
    pass