#!/bin/sh
# =============================================================================
# CronJob "sincronizar-consumos" (cada hora): trae de la comercializadora las
# lecturas de ayer y hoy de cada contrato y las guarda en MongoDB vía
# consumption-service. Repetir un rango no duplica lecturas.
#
# Contratos = viviendas con número de contrato + comercializadora, más clientes
# con contrato (de ellos sale id_cliente, que se usa para resolver la tarifa).
#
# Corre en postgres:*-alpine (psql + wget de busybox). Variables:
#   PGHOST, PGUSER, PGPASSWORD, PGDATABASE   conexión a PostgreSQL
#   CONSUMPTION_URL                          ej. http://harmoniwatts-consumption-service:8001
#   DIAS_ATRAS (opcional, 1)                 días previos a hoy que se vuelven a pedir
# =============================================================================
set -eu

DIAS_ATRAS="${DIAS_ATRAS:-1}"
URL="${CONSUMPTION_URL%/}/api/v1/consumption/sync/manual/contrato"

# Fechas en hora de Colombia (la imagen no trae zonas horarias; las calcula PostgreSQL)
HOY="$(psql -Atc "SELECT (now() AT TIME ZONE 'America/Bogota')::date")"
DESDE="$(psql -Atc "SELECT (now() AT TIME ZONE 'America/Bogota')::date - ${DIAS_ATRAS}")"

CONTRATOS="$(psql -At -F ' ' <<'SQL'
WITH contratos AS (
    SELECT btrim(v.numero_contrato) AS no_contrato, upper(v.cod_comercializadora) AS cod
    FROM vivienda v
    WHERE v.numero_contrato IS NOT NULL AND btrim(v.numero_contrato) <> ''
      AND v.cod_comercializadora IS NOT NULL
    UNION
    SELECT btrim(c.no_contrato), upper(c.cod_comercializadora)
    FROM cliente c
    WHERE c.activo AND c.no_contrato IS NOT NULL AND btrim(c.no_contrato) <> ''
)
SELECT k.no_contrato, k.cod, coalesce(min(c.id_cliente)::text, '-')
FROM contratos k
LEFT JOIN cliente c
       ON btrim(c.no_contrato) = k.no_contrato AND upper(c.cod_comercializadora) = k.cod
GROUP BY k.no_contrato, k.cod
ORDER BY k.cod, k.no_contrato;
SQL
)"

if [ -z "$CONTRATOS" ]; then
  echo "[sincronizar-consumos] No hay contratos registrados; nada que sincronizar."
  exit 0
fi

total=0
fallidos=0
echo "[sincronizar-consumos] Rango ${DESDE} a ${HOY}"
# Sin pipe para que los contadores no queden en un subshell
while read -r contrato cod id_cliente; do
  [ -n "$contrato" ] || continue
  total=$((total + 1))
  if [ "$id_cliente" = "-" ]; then id_json=null; else id_json="$id_cliente"; fi
  body="{\"id_cliente\":${id_json},\"fecha_inicio\":\"${DESDE}\",\"fecha_fin\":\"${HOY}\"}"
  if resp="$(wget -q -T 300 -O - --header 'Content-Type: application/json' \
               --post-data "$body" "${URL}/${contrato}/${cod}" 2>&1)" \
     && echo "$resp" | grep -q '"estado":"completado"'; then
    echo "  OK    ${cod}/${contrato}"
  else
    fallidos=$((fallidos + 1))
    echo "  ERROR ${cod}/${contrato}: ${resp}"
  fi
done <<EOF
$CONTRATOS
EOF

echo "[sincronizar-consumos] ${total} contratos, ${fallidos} con error."
# Falla el Job solo si fallaron todos (p. ej. la API de la comercializadora caída)
[ "$fallidos" -lt "$total" ]
