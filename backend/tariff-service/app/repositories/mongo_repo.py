from pymongo import MongoClient
from app.models.domain import Tarifa

class MongoTarifasRepo:
    def __init__(self, uri: str, db: str = "tarifas"):
        self.col = MongoClient(uri)[db]["tarifas"]

    def guardar_tarifas(self, tarifas: list[Tarifa]) -> int:
        if not tarifas:
            return 0
        docs = [t.__dict__ for t in tarifas]
        self.col.insert_many(docs)
        return len(docs)

    def existe_publicacion(self, comercializador, anio, mes) -> bool:
        return self.col.find_one(
            {"comercializador": comercializador, "anio": anio, "mes": mes}
        ) is not None