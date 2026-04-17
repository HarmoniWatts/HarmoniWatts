#!/usr/bin/env bash
set -euo pipefail
# Crea la base `harmoniwatts` si no existe (solo en primer arranque con volumen vacío).
if ! psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" -tc "SELECT 1 FROM pg_database WHERE datname = 'harmoniwatts'" | grep -q 1; then
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" -c "CREATE DATABASE harmoniwatts;"
fi
