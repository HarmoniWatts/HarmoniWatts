FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# model/ (pickles entrenados) y data/ (CSV de entrenamiento) se montan como volúmenes
RUN mkdir -p model data \
    && useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/users/health/ || exit 1

# Entrenar con RandomForest puede tardar: timeout amplio
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "600", "server:app"]
