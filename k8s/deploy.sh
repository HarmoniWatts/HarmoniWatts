#!/usr/bin/env bash
# =============================================================================
# Despliega HarmoniWatts en el clúster k3s al que apunta el kubeconfig actual.
# Lo usa .github/workflows/deploy-azure.yml, pero también se puede correr a mano.
#
# Variables obligatorias:
#   APP_HOST            dominio público (ej. harmoniwatts.eastus2.cloudapp.azure.com)
#   LETSENCRYPT_EMAIL   correo para avisos de Let's Encrypt
#   IMAGE_REGISTRY      prefijo de imágenes (ej. ghcr.io/harmoniwatts)
#   IMAGE_TAG           tag de las imágenes (ej. el SHA del commit)
#   POSTGRES_USER, POSTGRES_PASSWORD, KC_ADMIN_USERNAME, KC_ADMIN_PASSWORD
# Opcionales:
#   GEMINI_API_KEY, OPENAI_API_KEY, MISTRAL_API_KEY
#   SMTP_HOST, SMTP_PORT, SMTP_FROM, SMTP_USER, SMTP_PASSWORD
#   GHCR_PULL_USER + GHCR_PULL_TOKEN  (solo si las imágenes de GHCR son privadas)
#   CERT_MANAGER_VERSION (por defecto v1.18.2)
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NS=harmoniwatts
CERT_MANAGER_VERSION="${CERT_MANAGER_VERSION:-v1.18.2}"

for v in APP_HOST LETSENCRYPT_EMAIL IMAGE_REGISTRY IMAGE_TAG \
         POSTGRES_USER POSTGRES_PASSWORD KC_ADMIN_USERNAME KC_ADMIN_PASSWORD; do
  if [ -z "${!v:-}" ]; then
    echo "::error::Falta la variable $v" >&2
    exit 1
  fi
done

log() { echo; echo "==> $*"; }

# Elige python3 o python (Windows/Git Bash)
PY=python3
command -v "$PY" >/dev/null 2>&1 || PY=python

# -----------------------------------------------------------------------------
log "cert-manager ${CERT_MANAGER_VERSION}"
kubectl apply -f "https://github.com/cert-manager/cert-manager/releases/download/${CERT_MANAGER_VERSION}/cert-manager.yaml"
for d in cert-manager cert-manager-webhook cert-manager-cainjector; do
  kubectl -n cert-manager rollout status "deploy/$d" --timeout=5m
done

sed "s|__LETSENCRYPT_EMAIL__|${LETSENCRYPT_EMAIL}|g" "$ROOT/k8s/cluster/cluster-issuer.yaml" | kubectl apply -f -
kubectl apply -f "$ROOT/k8s/cluster/headlamp-rbac.yaml"

# -----------------------------------------------------------------------------
log "Namespace, secretos y ConfigMaps"
kubectl apply -f "$ROOT/k8s/base/namespace.yaml"

secret_args=(
  --from-literal=POSTGRES_USER="$POSTGRES_USER"
  --from-literal=POSTGRES_PASSWORD="$POSTGRES_PASSWORD"
  --from-literal=KC_ADMIN_USERNAME="$KC_ADMIN_USERNAME"
  --from-literal=KC_ADMIN_PASSWORD="$KC_ADMIN_PASSWORD"
)
for v in GEMINI_API_KEY OPENAI_API_KEY MISTRAL_API_KEY SMTP_HOST SMTP_PORT SMTP_FROM SMTP_USER SMTP_PASSWORD; do
  if [ -n "${!v:-}" ]; then secret_args+=(--from-literal="$v=${!v}"); fi
done
kubectl -n "$NS" create secret generic harmoniwatts-secrets "${secret_args[@]}" \
  --dry-run=client -o yaml | kubectl apply --server-side --force-conflicts -f -

if [ -n "${GHCR_PULL_TOKEN:-}" ]; then
  kubectl -n "$NS" create secret docker-registry ghcr-pull \
    --docker-server=ghcr.io \
    --docker-username="${GHCR_PULL_USER:-github}" \
    --docker-password="$GHCR_PULL_TOKEN" \
    --dry-run=client -o yaml | kubectl apply --server-side --force-conflicts -f -
fi

# Secreto del cliente "headlamp" en Keycloak: se genera la primera vez y se conserva
if ! kubectl -n "$NS" get secret headlamp-oidc >/dev/null 2>&1; then
  kubectl -n "$NS" create secret generic headlamp-oidc \
    --from-literal=client-secret="$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')"
fi

kubectl -n "$NS" create configmap postgres-init \
  --from-file=02-harmoniwatts-db.sh="$ROOT/docker/postgres/init-harmoniwatts-db.sh" \
  --dry-run=client -o yaml | kubectl apply --server-side --force-conflicts -f -

kubectl -n "$NS" create configmap mongo-seed \
  --from-file=consumos.json="$ROOT/BD/datos/harmoniwatts.consumos_enriquecidos.json" \
  --from-file=shift-timestamps.js="$ROOT/docker/mongo/shift-timestamps.js" \
  --from-file=reconcile-contexto.js="$ROOT/docker/mongo/reconcile-contexto.js" \
  --dry-run=client -o yaml | kubectl apply --server-side --force-conflicts -f -

# Realm: agrega el dominio público al cliente del SPA (redirects, CORS, logout)
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
"$PY" - "$ROOT/keycloak-realm/realm-export.json" "$WORK/realm-export.json" "$APP_HOST" <<'EOF'
import json, sys
src, dst, host = sys.argv[1], sys.argv[2], sys.argv[3]
origin = f"https://{host}"
with open(src, encoding="utf-8") as f:
    realm = json.load(f)
for c in realm.get("clients", []):
    if c.get("clientId") != "harmoniwatts-frontend":
        continue
    c["rootUrl"] = c["baseUrl"] = c["adminUrl"] = origin
    c["redirectUris"] = sorted(set(c.get("redirectUris", [])) | {f"{origin}/*"})
    c["webOrigins"] = sorted(set(c.get("webOrigins", [])) | {origin})
    attrs = c.setdefault("attributes", {})
    uris = [u for u in attrs.get("post.logout.redirect.uris", "").split("##") if u]
    attrs["post.logout.redirect.uris"] = "##".join(sorted(set(uris) | {f"{origin}/*"}))
realm["sslRequired"] = "external"
with open(dst, "w", encoding="utf-8") as f:
    json.dump(realm, f, ensure_ascii=False)
EOF
kubectl -n "$NS" create configmap keycloak-realm \
  --from-file=realm-export.json="$WORK/realm-export.json" \
  --dry-run=client -o yaml | kubectl apply --server-side --force-conflicts -f -

# -----------------------------------------------------------------------------
log "Manifiestos (imágenes ${IMAGE_REGISTRY}/harmoniwatts-*:${IMAGE_TAG})"
# Los Jobs son inmutables: se borra el seed anterior para volver a correrlo
kubectl -n "$NS" delete job mongo-seed --ignore-not-found

OVERLAY="$ROOT/k8s/.generated"
rm -rf "$OVERLAY"
mkdir -p "$OVERLAY"
{
  echo "apiVersion: kustomize.config.k8s.io/v1beta1"
  echo "kind: Kustomization"
  echo "resources:"
  echo "  - ../base"
  echo "images:"
  for svc in frontend harmoni-register vivienda-api electrodomesticos-api \
             consumption-service insights-service tariff-service prediction-service; do
    echo "  - name: harmoniwatts/${svc}"
    echo "    newName: ${IMAGE_REGISTRY}/harmoniwatts-${svc}"
    echo "    newTag: \"${IMAGE_TAG}\""
  done
} > "$OVERLAY/kustomization.yaml"

kubectl kustomize "$OVERLAY" | sed "s|__APP_HOST__|${APP_HOST}|g" | kubectl apply -f -
rm -rf "$OVERLAY"

# -----------------------------------------------------------------------------
log "Esperando a que los servicios queden listos"
kubectl -n "$NS" rollout status statefulset/postgres --timeout=5m
kubectl -n "$NS" rollout status statefulset/mongodb --timeout=5m
failed=()
for d in keycloak harmoni-register vivienda-api electrodomesticos-api consumption-service \
         insights-service tariff-service prediction-service frontend headlamp; do
  kubectl -n "$NS" rollout status "deployment/$d" --timeout=10m || failed+=("$d")
done

# -----------------------------------------------------------------------------
log "Keycloak: cliente OIDC de Headlamp (realm master)"
# Idempotente: crea o actualiza el cliente "headlamp", el mapper de grupos y el
# grupo "k8s-admins" (con el administrador de Keycloak como miembro). Usa las
# credenciales de administrador que el pod de Keycloak ya tiene en su entorno.
HEADLAMP_SECRET="$(kubectl -n "$NS" get secret headlamp-oidc -o jsonpath='{.data.client-secret}' | base64 -d)"
if ! kubectl -n "$NS" exec deploy/keycloak -- bash -c "$(cat "$ROOT/k8s/keycloak-headlamp.sh")" \
     keycloak-headlamp "$APP_HOST" "$HEADLAMP_SECRET"; then
  echo "::warning::No se pudo configurar el cliente de Headlamp en Keycloak (¿cambió la contraseña del admin?). El resto del despliegue no se ve afectado."
fi

kubectl -n "$NS" get pods -o wide

if [ ${#failed[@]} -gt 0 ]; then
  echo
  echo "::error::No quedaron listos: ${failed[*]}"
  echo "Si es el primer despliegue, las APIs Spring y tariff-service fallan hasta que la base"
  echo "'harmoniwatts' tenga el esquema: restaura un snapshot con scripts/k8s/restore-postgres.sh"
  echo "(ver k8s/README.md). Los pods se recuperan solos después del restore."
  echo "Logs: kubectl -n $NS logs deploy/<nombre> --tail=100"
  exit 1
fi

echo
echo "Listo: https://${APP_HOST}"
