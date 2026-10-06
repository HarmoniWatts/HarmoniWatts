from sqlalchemy.orm import Session
from app.models.sql_models import TarifaSQL
from app.models.domain import Tarifa

class SQLTarifasRepo:
    def __init__(self, session: Session):
        self.session = session

    def guardar_tarifas(self, tarifas: list[Tarifa]) -> int:
        self.session.bulk_save_objects([TarifaSQL(**t.__dict__) for t in tarifas])
        self.session.commit()
        return len(tarifas)

    def existe_publicacion(self, comercializador, anio, mes) -> bool:
        return self.session.query(TarifaSQL).filter_by(
            comercializador=comercializador, anio=anio, mes=mes
        ).first() is not None