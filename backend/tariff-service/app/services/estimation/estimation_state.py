import threading
from datetime import datetime
from typing import Any, Optional

_lock = threading.Lock()
_store: dict[str, dict[str, Any]] = {}


class EstimationStateStore:
    @classmethod
    def crear(cls, id_estimacion: str, datos_iniciales: dict) -> None:
        with _lock:
            _store[id_estimacion] = {
                **datos_iniciales,
                "estado": "pendiente",
                "tarifas_estimadas": 0,
                "tarifas_persistidas": 0,
                "tarifas": [],
                "errores": [],
                "mensaje": "En cola",
                "creado_en": datetime.utcnow().isoformat(),
                "actualizado_en": datetime.utcnow().isoformat(),
            }

    @classmethod
    def actualizar(cls, id_estimacion: str, **campos) -> None:
        with _lock:
            if id_estimacion in _store:
                _store[id_estimacion].update(campos)
                _store[id_estimacion]["actualizado_en"] = datetime.utcnow().isoformat()

    @classmethod
    def obtener(cls, id_estimacion: str) -> Optional[dict]:
        with _lock:
            return _store.get(id_estimacion)