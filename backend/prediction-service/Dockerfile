# prediction-service: FastAPI + modelo MLflow (app/model, incluido en la imagen).
# Python 3.13 = versión con que se guardó el modelo (app/model/conda.yaml).
FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

# PyTorch solo-CPU (~200 MB) en vez del paquete de PyPI con CUDA (~2 GB)
RUN pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/

# La configuración llega por variables de entorno (docker-compose / k8s); sin ellas se usan
# los valores por defecto de app/config.py (modelo local en app/model).
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
