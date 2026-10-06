from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Documento:
    id: int
    titulo: str
    url: str
    creado: datetime
    actualizado: datetime
    comercializador: str   # "enertotales", "otro", ...

@dataclass
class Tarifa:
    comercializador: str
    anio: int
    mes: int
    dia: Optional[int]
    variable: str          # nombre de la columna/fila de la tabla
    valor: float
    unidad: Optional[str]
    tabla_origen: int      # índice de tabla en el PDF
    extraido_en: datetime