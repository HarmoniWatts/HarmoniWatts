class PredictionError(Exception):
    """Error base del prediction-service."""
    pass


class ModelNotLoadedError(PredictionError):
    """El modelo no está cargado."""
    pass


class InsufficientHistoryError(PredictionError):
    """El medidor no tiene suficiente historia."""
    def __init__(self, meter_no: str, horas: int):
        self.meter_no = meter_no
        self.horas = horas
        super().__init__(
            f"Medidor/Contrato {meter_no} tiene {horas} h de historia; "
            f"se requieren al menos 504 h"
        )


class ConsumptionServiceError(PredictionError):
    """Error al consultar el consumption-service."""
    pass