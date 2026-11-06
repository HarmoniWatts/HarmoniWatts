#!/usr/bin/env bash
# =============================================================================
# Obtiene el kubeconfig de k3s desde la VM (vía az vm run-command, sin SSH), lo
# guarda en ~/.kube/harmoniwatts-azure.yaml apuntando al dominio público y, si
# `gh` está autenticado, lo sube como secreto KUBECONFIG del environment de GitHub.
#
# Uso: infra/azure/get-kubeconfig.sh   (mismas variables RG/VM/DNS_LABEL/LOCATION
#      que provision.sh si las cambiaste)
# =============================================================================
set -euo pipefail

LOCATION="${LOCATION:-eastus2}"
RG="${RG:-rg-harmoniwatts}"
VM="${VM:-vm-harmoniwatts}"
DNS_LABEL="${DNS_LABEL:-harmoniwatts}"
GITHUB_REPO="${GITHUB_REPO:-HarmoniWatts/HarmoniWatts}"
GITHUB_ENV="${GITHUB_ENV_NAME:-azure}"
APP_HOST="${DNS_LABEL}.${LOCATION}.cloudapp.azure.com"
OUT="${OUT:-$HOME/.kube/harmoniwatts-azure.yaml}"

echo "Leyendo /etc/rancher/k3s/k3s.yaml de $VM..."
RAW="$(az vm run-command invoke -g "$RG" -n "$VM" --command-id RunShellScript \
  --scripts "cloud-init status --wait >/dev/null 2>&1; cat /etc/rancher/k3s/k3s.yaml" \
  --query "value[0].message" -o tsv)"

# La salida viene como "Enable succeeded: [stdout] ... [stderr] ..."
KUBECONFIG_CONTENT="$(printf '%s\n' "$RAW" | sed -n '/^\[stdout\]/,/^\[stderr\]/p' | sed '1d;$d' \
  | sed "s|https://127.0.0.1:6443|https://${APP_HOST}:6443|")"

if ! printf '%s' "$KUBECONFIG_CONTENT" | grep -q "certificate-authority-data"; then
  echo "No se pudo leer el kubeconfig (¿k3s terminó de instalarse?). Salida:" >&2
  printf '%s\n' "$RAW" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUT")"
umask 077
printf '%s\n' "$KUBECONFIG_CONTENT" > "$OUT"
echo "Guardado en $OUT"
echo "Prueba:  KUBECONFIG=$OUT kubectl get nodes"

if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  gh secret set KUBECONFIG -R "$GITHUB_REPO" --env "$GITHUB_ENV" < "$OUT"
  echo "Secreto KUBECONFIG actualizado en el environment '${GITHUB_ENV}'."
else
  echo "Sube el contenido de $OUT como secreto KUBECONFIG del environment '${GITHUB_ENV}'."
fi
