#!/bin/sh
# =============================================================================
# CronJob "actualizar-tarifas" (semanal): para cada comercializadora activa pide a
# tariff-service que descargue y procese los PDFs de tarifas publicados desde el
# primer día del mes anterior hasta hoy. Las tarifas que ya existen no se duplican.
#
# La extracción corre en segundo plano en tariff-service; el script consulta su
# estado hasta que termina para que el Job refleje el resultado.
#
# Corre en postgres:*-alpine (psql + wget de busybox). Variables:
#   PGHOST, PGUSER, PGPASSWORD, PGDATABASE   conexión a PostgreSQL
#   TARIFF_URL                               ej. http://harmoniwatts-tariff-service:8006
#   MAX_ESPERA_SEG (opcional, 1800)          tiempo máximo por comercializadora
# =============================================================================
set -eu

MAX_ESPERA_SEG="${MAX_ESPERA_SEG:-1800}"
URL="${TARIFF_URL%/}/api/v1/tariff/extraction"

DESDE="$(psql -Atc "SELECT (date_trunc('month', now() AT TIME ZONE 'America/Bogota') - interval '1 month')::date")"
HOY="$(psql -Atc "SELECT (now() AT TIME ZONE 'America/Bogota')::date")"
COMERCIALIZADORAS="$(psql -Atc "SELECT cod_comercializadora FROM comercializadora WHERE activo ORDER BY 1")"

if [ -z "$COMERCIALIZADORAS" ]; then
  echo "[actualizar-tarifas] No hay comercializadoras activas."
  exit 0
fi

campo() { # campo <json> <nombre>: valor de texto de un campo del JSON
  echo "$1" | sed -n "s/.*\"$2\":\"\([^\"]*\)\".*/\1/p"
}
numero() { # numero <json> <nombre>
  echo "$1" | sed -n "s/.*\"$2\":\([0-9]*\).*/\1/p"
}

fallidos=0
echo "[actualizar-tarifas] PDFs publicados entre ${DESDE} y ${HOY}"
for cod in $COMERCIALIZADORAS; do
  body="{\"comercializadora_cod\":\"${cod}\",\"fecha_inicio\":\"${DESDE}\",\"fecha_fin\":\"${HOY}\"}"
  if ! resp="$(wget -q -T 60 -O - --header 'Content-Type: application/json' \
                 --post-data "$body" "${URL}/manual" 2>&1)"; then
    echo "  ERROR ${cod}: no se pudo iniciar la extracción: ${resp}"
    fallidos=$((fallidos + 1))
    continue
  fi
  id="$(campo "$resp" id_extraccion)"
  echo "  ${cod}: extracción ${id} iniciada"

  estado=pendiente
  esperado=0
  while [ "$estado" = pendiente ] || [ "$estado" = en_proceso ]; do
    if [ "$esperado" -ge "$MAX_ESPERA_SEG" ]; then
      estado=timeout
      break
    fi
    sleep 15
    esperado=$((esperado + 15))
    resp="$(wget -q -T 30 -O - "${URL}/estado/${id}" 2>&1)" || continue
    estado="$(campo "$resp" estado)"
  done

  case "$estado" in
    completado)
      echo "  OK    ${cod}: $(numero "$resp" tarifas_extraidas) tarifas leídas," \
           "$(numero "$resp" tarifas_insertadas) nuevas"
      ;;
    *)
      echo "  ERROR ${cod}: estado ${estado}: ${resp}"
      fallidos=$((fallidos + 1))
      ;;
  esac
done

[ "$fallidos" -eq 0 ]
