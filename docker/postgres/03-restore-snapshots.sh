#!/usr/bin/env bash
# Restaura dumps de docker/snapshots/postgres en el primer arranque (volumen vacío).
# Se ejecuta después de 02-harmoniwatts-db.sh (crea la BD harmoniwatts).
set -euo pipefail

SNAP_DIR="/docker-entrypoint-initdb.d/snapshots"
KC_DB="${POSTGRES_DB:-keycloak_db}"

restore_one() {
  local db="$1"
  local file="$2"
  if [ ! -f "$file" ]; then
    echo "[snapshots] No hay dump para $db ($file); se omite restore."
    return 0
  fi
  echo "[snapshots] Restaurando $db desde $(basename "$file")..."
  # --no-owner/--no-acl: portable entre máquinas con el mismo POSTGRES_USER del .env
  pg_restore --username="$POSTGRES_USER" --dbname="$db" --no-owner --no-acl --verbose "$file" \
    || echo "[snapshots] Aviso: pg_restore de $db terminó con código $? (revisar si faltan objetos)."
  echo "[snapshots] $db listo."
}

if [ ! -d "$SNAP_DIR" ]; then
  echo "[snapshots] Carpeta $SNAP_DIR no montada; solo schema vacío + CREATE DATABASE."
  exit 0
fi

restore_one "$KC_DB" "$SNAP_DIR/keycloak_db.dump"
restore_one "harmoniwatts" "$SNAP_DIR/harmoniwatts.dump"

echo "[snapshots] Restore Postgres finalizado."
