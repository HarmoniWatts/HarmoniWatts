# app/services/extraction/extraction_state.py

from typing import Dict, Any
from datetime import datetime
from threading import Lock


class ExtractionStateStore:
    """Almacén en memoria del estado de extracciones."""
    
    _store: Dict[str, Dict[str, Any]] = {}
    _lock = Lock()
    
    @classmethod
    def crear(cls, id_extraccion: str, datos_iniciales: Dict[str, Any]):
        with cls._lock:
            cls._store[id_extraccion] = {
                **datos_iniciales,
                'estado': 'pendiente',
                'creada_en': datetime.now().isoformat(),
                'actualizada_en': datetime.now().isoformat(),
            }
    
    @classmethod
    def actualizar(cls, id_extraccion: str, **kwargs):
        with cls._lock:
            if id_extraccion in cls._store:
                cls._store[id_extraccion].update(kwargs)
                cls._store[id_extraccion]['actualizada_en'] = datetime.now().isoformat()
    
    @classmethod
    def obtener(cls, id_extraccion: str) -> Dict[str, Any] | None:
        return cls._store.get(id_extraccion)
    
    @classmethod
    def listar(cls) -> list:
        return list(cls._store.values())