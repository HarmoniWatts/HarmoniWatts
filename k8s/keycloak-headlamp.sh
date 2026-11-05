#!/usr/bin/env bash
# =============================================================================
# Se ejecuta DENTRO del pod de Keycloak (lo llama k8s/deploy.sh con kubectl exec).
# Crea o actualiza, en el realm "master":
#   - el cliente OIDC "headlamp" (confidencial, PKCE, redirect a /headlamp/oidc-callback,
#     tokens de 30 min: el realm master los da de 1 min y Headlamp perdía la conexión)
#   - un mapper que publica los grupos del usuario en el claim "groups"
#   - el grupo "k8s-admins" (administradores del clúster, ver k8s/cluster/headlamp-rbac.yaml)
#     con el administrador de Keycloak como miembro
# Es idempotente: se puede ejecutar en cada despliegue.
#
# Uso: keycloak-headlamp.sh <APP_HOST> <CLIENT_SECRET>
# =============================================================================
set -euo pipefail

APP_HOST="$1"
SECRET="$2"
REALM=master
KC=/opt/keycloak/bin/kcadm.sh
export HOME=/tmp

"$KC" config credentials --server http://localhost:8080/auth --realm master \
  --user "$KC_BOOTSTRAP_ADMIN_USERNAME" --password "$KC_BOOTSTRAP_ADMIN_PASSWORD" >/dev/null

client_id() {
  "$KC" get clients -r "$REALM" -q clientId=headlamp --fields id --format csv --noquotes
}

CID="$(client_id)"
if [ -z "$CID" ]; then
  "$KC" create clients -r "$REALM" -s clientId=headlamp -s protocol=openid-connect >/dev/null
  CID="$(client_id)"
  echo "Cliente headlamp creado."
fi

"$KC" update "clients/$CID" -r "$REALM" \
  -s name=Headlamp -s enabled=true -s publicClient=false \
  -s standardFlowEnabled=true -s directAccessGrantsEnabled=false \
  -s implicitFlowEnabled=false -s serviceAccountsEnabled=false \
  -s "secret=$SECRET" \
  -s "rootUrl=https://$APP_HOST/headlamp" \
  -s "redirectUris=[\"https://$APP_HOST/headlamp/oidc-callback\"]" \
  -s "webOrigins=[\"https://$APP_HOST\"]" \
  -s 'attributes."pkce.code.challenge.method"=S256' \
  -s 'attributes."access.token.lifespan"=1800' \
  -s "attributes.\"post.logout.redirect.uris\"=https://$APP_HOST/headlamp/*"

if ! "$KC" get "clients/$CID/protocol-mappers/models" -r "$REALM" --fields name --format csv --noquotes \
     | grep -qx groups; then
  "$KC" create "clients/$CID/protocol-mappers/models" -r "$REALM" \
    -s name=groups -s protocol=openid-connect -s protocolMapper=oidc-group-membership-mapper \
    -s 'config."claim.name"=groups' -s 'config."full.path"=false' \
    -s 'config."id.token.claim"=true' -s 'config."access.token.claim"=true' \
    -s 'config."userinfo.token.claim"=true' >/dev/null
  echo "Mapper de grupos creado."
fi

group_id() {
  "$KC" get groups -r "$REALM" -q search=k8s-admins -q exact=true --fields id,name --format csv --noquotes \
    | sed -n 's/^\([^,]*\),k8s-admins$/\1/p'   # la imagen de Keycloak no trae awk
}

GID="$(group_id)"
if [ -z "$GID" ]; then
  "$KC" create groups -r "$REALM" -s name=k8s-admins >/dev/null
  GID="$(group_id)"
  echo "Grupo k8s-admins creado."
fi

ADMIN_ID="$("$KC" get users -r "$REALM" -q "username=$KC_BOOTSTRAP_ADMIN_USERNAME" -q exact=true \
  --fields id --format csv --noquotes)"
if [ -n "$ADMIN_ID" ]; then
  "$KC" update "users/$ADMIN_ID/groups/$GID" -r "$REALM" \
    -s realm="$REALM" -s userId="$ADMIN_ID" -s groupId="$GID" -n
fi

echo "Keycloak listo para Headlamp: https://$APP_HOST/headlamp"
