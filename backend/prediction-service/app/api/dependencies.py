from fastapi import Depends

from app.services.prediction_service import PredictionService


def get_prediction_service() -> PredictionService:
    return PredictionService()