#!/usr/bin/env bash
# =============================================================================
# Crea la infraestructura de HarmoniWatts en la suscripción de Azure activa:
#   - Grupo de recursos, IP pública estática con nombre DNS, NSG (80/443 abiertos,
#     22 y 6443 solo desde tu IP) y una VM Ubuntu con k3s (cloud-init.yaml).
#   - Apagado automático diario de la VM.
#   - Identidad para GitHub Actions por OIDC (sin contraseñas): identidad
#     administrada + credencial federada para el environment "azure" del
#     repositorio, con rol Contributor solo sobre el grupo de recursos. No requiere
#     permisos en Entra ID (sirve aunque seas invitado en el directorio).
#   - Si `gh` está autenticado, guarda los IDs y variables en el environment de GitHub.
#
# Requisitos: az (con `az login` hecho) y, opcional, gh (`gh auth login`).
# Uso (Git Bash):
#   az account set --subscription "<id o nombre de la suscripción>"
#   infra/azure/provision.sh
#
# Para cambiar de suscripción (ej. de la prueba gratuita a Azure for Students):
# selecciona la nueva con `az account set` y vuelve a ejecutar este script; luego
# repite los pasos de k8s/README.md (kubeconfig + primer despliegue).
# =============================================================================
set -euo pipefail
# Git Bash convierte argumentos como /subscriptions/... en rutas de Windows
export MSYS_NO_PATHCONV=1

LOCATION="${LOCATION:-eastus2}"
RG="${RG:-rg-harmoniwatts}"
VM="${VM:-vm-harmoniwatts}"
VM_SIZE="${VM_SIZE:-Standard_D2as_v7}"       # 2 vCPU / 8 GB (la serie B no está habilitada en la prueba gratuita)
DISK_GB="${DISK_GB:-64}"
DNS_LABEL="${DNS_LABEL:-harmoniwatts}"         # debe ser único en la región
GITHUB_REPO="${GITHUB_REPO:-HarmoniWatts/HarmoniWatts}"
GITHUB_ENV="${GITHUB_ENV_NAME:-azure}"
SHUTDOWN_UTC="${SHUTDOWN_UTC:-0400}"           # 04:00 UTC = 23:00 hora Colombia
ADMIN_IP="${ADMIN_IP:-$(curl -s https://api.ipify.org)}"

NSG="nsg-${VM}"
PIP="pip-${VM}"
IDENTITY="id-github-${RG}"
APP_HOST="${DNS_LABEL}.${LOCATION}.cloudapp.azure.com"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SUB_ID="$(az account show --query id -o tsv)"
SUB_NAME="$(az account show --query name -o tsv)"
TENANT_ID="$(az account show --query tenantId -o tsv)"

echo "Suscripción : $SUB_NAME ($SUB_ID)"
echo "Región      : $LOCATION   VM: $VM ($VM_SIZE)   Dominio: $APP_HOST"
echo "Tu IP       : $ADMIN_IP (SSH y API de Kubernetes)"
echo

echo "==> Proveedores de recursos (necesario en suscripciones nuevas)"
for ns in Microsoft.Compute Microsoft.Network Microsoft.ManagedIdentity Microsoft.DevTestLab; do
  az provider register --namespace "$ns" --wait -o none
done

echo "==> Grupo de recursos"
az group create -n "$RG" -l "$LOCATION" -o none

echo "==> Red: IP pública y NSG"
# Si falla por "DnsRecordInUse", el nombre ya existe en la región: usa DNS_LABEL=otro-nombre
az network public-ip create -g "$RG" -n "$PIP" --sku Standard --allocation-method Static \
  --dns-name "$DNS_LABEL" -o none
az network nsg create -g "$RG" -n "$NSG" -o none
az network nsg rule create -g "$RG" --nsg-name "$NSG" -n allow-http-https --priority 100 \
  --access Allow --protocol Tcp --direction Inbound --destination-port-ranges 80 443 -o none
az network nsg rule create -g "$RG" --nsg-name "$NSG" -n allow-admin --priority 110 \
  --access Allow --protocol Tcp --direction Inbound --destination-port-ranges 22 6443 \
  --source-address-prefixes "$ADMIN_IP" -o none

echo "==> VM con k3s (puede tardar unos minutos)"
CLOUD_INIT="$(mktemp)"
trap 'rm -f "$CLOUD_INIT"' EXIT
sed "s|__APP_HOST__|${APP_HOST}|g" "$HERE/cloud-init.yaml" > "$CLOUD_INIT"
# En Git Bash, az (programa de Windows) necesita la ruta en formato Windows
CLOUD_INIT_ARG="$CLOUD_INIT"
if command -v cygpath >/dev/null 2>&1; then CLOUD_INIT_ARG="$(cygpath -w "$CLOUD_INIT")"; fi
if ! az vm show -g "$RG" -n "$VM" >/dev/null 2>&1; then
  az vm create -g "$RG" -n "$VM" \
    --image Ubuntu2404 --size "$VM_SIZE" \
    --admin-username azureuser --generate-ssh-keys \
    --os-disk-size-gb "$DISK_GB" --storage-sku StandardSSD_LRS \
    --public-ip-address "$PIP" --nsg "$NSG" \
    --custom-data "$CLOUD_INIT_ARG" -o none
else
  echo "    La VM ya existe; se omite."
fi
az vm auto-shutdown -g "$RG" -n "$VM" --time "$SHUTDOWN_UTC" -o none

echo "==> Identidad OIDC para GitHub Actions"
az identity create -g "$RG" -n "$IDENTITY" -o none
APP_ID="$(az identity show -g "$RG" -n "$IDENTITY" --query clientId -o tsv)"
PRINCIPAL_ID="$(az identity show -g "$RG" -n "$IDENTITY" --query principalId -o tsv)"
SUBJECT="repo:${GITHUB_REPO}:environment:${GITHUB_ENV}"
az identity federated-credential create -g "$RG" --identity-name "$IDENTITY"   -n "github-${GITHUB_ENV}" --issuer https://token.actions.githubusercontent.com   --subject "$SUBJECT" --audiences api://AzureADTokenExchange -o none
# GitHub puede emitir el subject con IDs inmutables: repo:Owner@<id>/Repo@<id>:environment:...
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  IDS="$(gh api "repos/${GITHUB_REPO}" --jq '"\(.owner.id) \(.id)"')"
  SUBJECT_IDS="repo:${GITHUB_REPO%%/*}@${IDS%% *}/${GITHUB_REPO##*/}@${IDS##* }:environment:${GITHUB_ENV}"
  az identity federated-credential create -g "$RG" --identity-name "$IDENTITY"     -n "github-${GITHUB_ENV}-ids" --issuer https://token.actions.githubusercontent.com     --subject "$SUBJECT_IDS" --audiences api://AzureADTokenExchange -o none
fi
RG_ID="$(az group show -n "$RG" --query id -o tsv)"
# La identidad recién creada puede tardar unos segundos en propagarse
for i in 1 2 3 4 5 6; do
  if az role assignment create --assignee-object-id "$PRINCIPAL_ID" --assignee-principal-type ServicePrincipal        --role Contributor --scope "$RG_ID" -o none 2>/dev/null; then
    break
  fi
  [ "$i" = 6 ] && { echo "No se pudo asignar el rol Contributor a la identidad" >&2; exit 1; }
  sleep 10
done

echo
echo "Infraestructura lista. Dominio: https://${APP_HOST}"
echo

if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  echo "==> Configurando el environment '${GITHUB_ENV}' en ${GITHUB_REPO}"
  gh api -X PUT "repos/${GITHUB_REPO}/environments/${GITHUB_ENV}" >/dev/null
  gh secret set AZURE_CLIENT_ID       -R "$GITHUB_REPO" --env "$GITHUB_ENV" -b "$APP_ID"
  gh secret set AZURE_TENANT_ID       -R "$GITHUB_REPO" --env "$GITHUB_ENV" -b "$TENANT_ID"
  gh secret set AZURE_SUBSCRIPTION_ID -R "$GITHUB_REPO" --env "$GITHUB_ENV" -b "$SUB_ID"
  gh variable set AZURE_RESOURCE_GROUP -R "$GITHUB_REPO" --env "$GITHUB_ENV" -b "$RG"
  gh variable set AZURE_VM_NAME        -R "$GITHUB_REPO" --env "$GITHUB_ENV" -b "$VM"
  gh variable set AZURE_NSG_NAME       -R "$GITHUB_REPO" --env "$GITHUB_ENV" -b "$NSG"
  gh variable set APP_HOST             -R "$GITHUB_REPO" --env "$GITHUB_ENV" -b "$APP_HOST"
  echo "    Hecho. Faltan los secretos de la aplicación (ver k8s/README.md)."
else
  cat <<EOF
gh no está disponible: crea el environment '${GITHUB_ENV}' en GitHub y agrega:
  Secretos : AZURE_CLIENT_ID=${APP_ID}
             AZURE_TENANT_ID=${TENANT_ID}
             AZURE_SUBSCRIPTION_ID=${SUB_ID}
  Variables: AZURE_RESOURCE_GROUP=${RG}  AZURE_VM_NAME=${VM}
             AZURE_NSG_NAME=${NSG}  APP_HOST=${APP_HOST}
EOF
fi

echo
echo "Siguiente paso: infra/azure/get-kubeconfig.sh (cuando cloud-init termine, ~3-5 min)."
