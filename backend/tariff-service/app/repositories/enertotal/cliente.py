import time, requests
from datetime import date
from app.models.domain import Documento
from app.repositories.enertotales.mapper import mapear_documento

class EnertotalesAPI:
    comercializador = "enertotales"

    def __init__(self, base_url: str, headers: dict, timeout=30, limit=100):
        self.base_url = base_url
        self.headers = headers
        self.timeout = timeout
        self.limit = limit

    def listar_documentos(self, filtros, desde=None):
        vistos = {}
        for filtro in filtros:
            for raw in self._paginar(filtro):
                vistos[raw["id"]] = raw
        docs = [mapear_documento(d) for d in vistos.values()]
        if desde:
            docs = [d for d in docs if self._mes_anio(d) >= desde]
        return docs

    def _paginar(self, filtro):
        page = 1
        while True:
            r = requests.get(
                self.base_url,
                params={
                    "where[title][contains]": filtro,
                    "sort": "-createdAt",
                    "limit": self.limit,
                    "page": page,
                },
                headers=self.headers, timeout=self.timeout,
            )
            r.raise_for_status()
            data = r.json()
            yield from data.get("docs", [])
            if not data.get("hasNextPage"):
                break
            page += 1
            time.sleep(0.3)

    def descargar_pdf(self, url):
        r = requests.get(url, headers=self.headers, timeout=60)
        r.raise_for_status()
        return r.content

    @staticmethod
    def _mes_anio(doc: Documento) -> date:
        return date(doc.creado.year, doc.creado.month, 1)