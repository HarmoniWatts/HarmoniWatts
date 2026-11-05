#!/usr/bin/env bash
# =============================================================================
# Restaura los snapshots de PostgreSQL (los de scripts/export-snapshots.sh) en el
# clúster k3s al que apunta el kubeconfig actual.
#
# Uso:  scripts/k8s/restore-postgres.sh docker/snapshots/postgres
#       (carpeta con keycloak_db.dump y/o harmoniwatts.dump, formato pg_dump -Fc)
#
# Reemplaza los objetos existentes (--clean). Después reinicia Keycloak y las APIs.
# =============================================================================
set -euo pipefail
export MSYS_NO_PATHCONV=1  # Git Bash: no convertir rutas /tmp/...

DIR="${1:-docker/snapshots/postgres}"
NS=harmoniwatts
POD=postgres-0

kubectl -n "$NS" wait --for=condition=Ready "pod/$POD" --timeout=5m

restore() {
  local db="$1" file="$DIR/$1.dump"
  if [ ! -f "$file" ]; then
    echo "[restore] No existe $file; se omite $db."
    return
  fi
  echo "[restore] $db <- $file"
  kubectl -n "$NS" cp "$file" "$POD:/tmp/$db.dump"
  kubectl -n "$NS" exec "$POD" -- sh -c \
    "pg_restore -U \"\$POSTGRES_USER\" -d $db --clean --if-exists --no-owner --no-acl /tmp/$db.dump; rm -f /tmp/$db.dump" \
    || echo "[restore] Aviso: pg_restore de $db terminó con advertencias (revisar arriba)."
}

restore keycloak_db
restore harmoniwatts

echo "[restore] Reiniciando servicios que usan PostgreSQL..."
kubectl -n "$NS" rollout restart deployment/keycloak deployment/vivienda-api \
  deployment/electrodomesticos-api deployment/tariff-service
echo "[restore] Listo."
