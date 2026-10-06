from typing import Protocol, Iterable
from datetime import date, datetime
from app.models.domain import Documento, Tarifa

class RepositorioTarifas(Protocol):
    """DRIVER: fuente externa."""
    comercializador: str
    def listar_documentos(self, filtros: list[str], desde: date | None = None) -> Iterable[Documento]: ...
    def descargar_pdf(self, url: str) -> bytes: ...

class RepositorioPersistencia(Protocol):
    """PERSISTENCIA (SQL primario o Mongo secundario)."""
    def existe_publicacion(self, comercializador: str, anio: int, mes: int) -> bool: ...
    def guardar_tarifas(self, tarifas: list[Tarifa]) -> int: ...