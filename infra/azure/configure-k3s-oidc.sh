#!/usr/bin/env bash
# =============================================================================
# Configura el API server de k3s (en la VM de Azure) para aceptar los tokens de
# Keycloak (realm "master", cliente "headlamp"). Así Headlamp puede entrar al
# clúster con el usuario que inicia sesión en Keycloak, y RBAC decide qué puede
# hacer (k8s/cluster/headlamp-rbac.yaml: grupo k8s-admins → cluster-admin).
#
# Usuarios y grupos del token llegan a Kubernetes con el prefijo "oidc:".
# Si k3s no arranca con la nueva configuración, el script la revierte solo.
#
# Uso (Git Bash, con `az login` hecho): infra/azure/configure-k3s-oidc.sh
# Lo llama provision.sh; se puede volver a ejecutar sin problema.
# =============================================================================
set -euo pipefail
export MSYS_NO_PATHCONV=1

RG="${RG:-rg-harmoniwatts}"
VM="${VM:-vm-harmoniwatts}"
LOCATION="${LOCATION:-eastus2}"
DNS_LABEL="${DNS_LABEL:-harmoniwatts}"
APP_HOST="${APP_HOST:-${DNS_LABEL}.${LOCATION}.cloudapp.azure.com}"

read -r -d '' REMOTE <<'EOF' || true
set -eu
APP_HOST="$1"
DIR=/etc/rancher/k3s
AUTHN="$DIR/authentication-config.yaml"
CFG="$DIR/config.yaml"
mkdir -p "$DIR"
cp -a "$CFG" "$CFG.bak" 2>/dev/null || : > "$CFG.bak"
cp -a "$AUTHN" "$AUTHN.bak" 2>/dev/null || : > "$AUTHN.bak"

write_authn() {
  cat > "$AUTHN" <<YAML
apiVersion: apiserver.config.k8s.io/$1
kind: AuthenticationConfiguration
jwt:
  - issuer:
      url: https://${APP_HOST}/auth/realms/master
      audiences: [headlamp]
    claimMappings:
      username: { claim: preferred_username, prefix: "oidc:" }
      groups: { claim: groups, prefix: "oidc:" }
YAML
}

grep -q 'authentication-config=' "$CFG" 2>/dev/null || cat >> "$CFG" <<YAML
kube-apiserver-arg:
  - authentication-config=${AUTHN}
YAML

ready() {
  for i in $(seq 1 36); do
    k3s kubectl get --raw /readyz >/dev/null 2>&1 && return 0
    sleep 5
  done
  return 1
}

for version in v1 v1beta1; do
  write_authn "$version"
  systemctl restart k3s || true
  if ready; then
    echo "k3s listo con AuthenticationConfiguration $version (issuer https://${APP_HOST}/auth/realms/master)"
    exit 0
  fi
  echo "k3s no arrancó con $version; probando la siguiente versión..."
done

echo "Revirtiendo la configuración anterior."
cp -a "$CFG.bak" "$CFG"
if [ -s "$AUTHN.bak" ]; then cp -a "$AUTHN.bak" "$AUTHN"; else rm -f "$AUTHN"; fi
systemctl restart k3s
ready || true
exit 1
EOF

echo "==> Configurando OIDC en el API server de k3s ($VM, issuer https://${APP_HOST}/auth/realms/master)"
out="$(az vm run-command invoke -g "$RG" -n "$VM" --command-id RunShellScript \
  --scripts "$REMOTE" --parameters "$APP_HOST" --query 'value[0].message' -o tsv)"
echo "$out"
echo "$out" | grep -q 'k3s listo con' || { echo "La configuración falló (ver arriba)." >&2; exit 1; }
