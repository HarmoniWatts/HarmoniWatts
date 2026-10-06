from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class TarifaSQL(Base):
    __tablename__ = "tarifas"

    id = Column(Integer, primary_key=True)
    comercializador = Column(String(50), nullable=False)
    anio = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)
    dia = Column(Integer, nullable=True)
    variable = Column(String(200), nullable=False)
    valor = Column(Float, nullable=False)
    unidad = Column(String(50), nullable=True)
    tabla_origen = Column(Integer, nullable=False)
    extraido_en = Column(DateTime, default=datetime.utcnow)
    sincronizado_en = Column(DateTime, nullable=True)   # 👈 marca de sync

    __table_args__ = (
        UniqueConstraint("comercializador", "anio", "mes", "variable", "dia",
                         name="uq_tarifa"),
        Index("ix_pub", "comercializador", "anio", "mes"),
        Index("ix_sync", "sincronizado_en"),
    )