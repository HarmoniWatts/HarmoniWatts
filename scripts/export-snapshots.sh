#!/usr/bin/env bash
# Exporta Postgres + Mongo a docker/snapshots/ (Linux/macOS o Git Bash).
# Uso desde la raíz HarmoniWatts: ./scripts/export-snapshots.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PG_CONTAINER="${PG_CONTAINER:-keycloak-postgres}"
MONGO_CONTAINER="${MONGO_CONTAINER:-harmoniwatts-mongodb}"
SNAP_ROOT="$ROOT/docker/snapshots"
PG_OUT="$SNAP_ROOT/postgres"
MONGO_OUT="$SNAP_ROOT/mongo"

need_running() {
  if ! docker ps --format '{{.Names}}' | grep -qx "$1"; then
    echo "Contenedor '$1' no está en marcha. Ejecuta: docker compose up -d" >&2
    exit 1
  fi
}

need_running "$PG_CONTAINER"
need_running "$MONGO_CONTAINER"

mkdir -p "$PG_OUT" "$MONGO_OUT"

PG_USER="${POSTGRES_USER:-postgres}"
PG_KC_DB="${POSTGRES_DB:-keycloak_db}"
if [ -f "$ROOT/.env" ]; then
  # shellcheck disable=SC1091
  set -a
  # Solo líneas KEY=VAL simples
  while IFS= read -r line; do
    case "$line" in
      POSTGRES_USER=*) PG_USER="${line#POSTGRES_USER=}" ;;
      POSTGRES_DB=*) PG_KC_DB="${line#POSTGRES_DB=}" ;;
    esac
  done < "$ROOT/.env"
  set +a
fi
PG_USER="${PG_USER%\"}"; PG_USER="${PG_USER#\"}"
PG_KC_DB="${PG_KC_DB%\"}"; PG_KC_DB="${PG_KC_DB#\"}"

echo "==> Export Postgres: $PG_KC_DB + harmoniwatts"
docker exec "$PG_CONTAINER" pg_dump -U "$PG_USER" -d "$PG_KC_DB" -Fc -f /tmp/keycloak_db.dump
docker cp "$PG_CONTAINER:/tmp/keycloak_db.dump" "$PG_OUT/keycloak_db.dump"
docker exec "$PG_CONTAINER" rm -f /tmp/keycloak_db.dump

docker exec "$PG_CONTAINER" pg_dump -U "$PG_USER" -d harmoniwatts -Fc -f /tmp/harmoniwatts.dump
docker cp "$PG_CONTAINER:/tmp/harmoniwatts.dump" "$PG_OUT/harmoniwatts.dump"
docker exec "$PG_CONTAINER" rm -f /tmp/harmoniwatts.dump

echo "==> Export Mongo: harmoniwatts"
docker exec "$MONGO_CONTAINER" rm -rf /tmp/mongo-dump
docker exec "$MONGO_CONTAINER" mongodump --db=harmoniwatts --out=/tmp/mongo-dump
rm -rf "$MONGO_OUT/harmoniwatts"
docker cp "$MONGO_CONTAINER:/tmp/mongo-dump/harmoniwatts" "$MONGO_OUT/harmoniwatts"
docker exec "$MONGO_CONTAINER" rm -rf /tmp/mongo-dump

cat > "$SNAP_ROOT/MANIFEST.txt" <<EOF
HarmoniWatts data snapshot
exported_at: $(date -Iseconds 2>/dev/null || date)
postgres_container: $PG_CONTAINER
postgres_user: $PG_USER
postgres_dumps:
  - ${PG_KC_DB}.dump
  - harmoniwatts.dump
mongo_container: $MONGO_CONTAINER
mongo_dump: mongo/harmoniwatts/
EOF

echo "OK. Snapshots en: $SNAP_ROOT"
