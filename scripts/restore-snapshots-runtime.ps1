#Requires -Version 5.1
<#
.SYNOPSIS
  Restaura snapshots en contenedores YA en marcha (sobrescribe datos).
  Preferible en PC nueva: dejar que el init de Compose restaure solo.

.DESCRIPTION
  Uso:
    .\scripts\restore-snapshots-runtime.ps1
  Aviso: borra/reemplaza datos actuales de Postgres (ambas BD) y Mongo.
#>
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$PgContainer = "keycloak-postgres"
$MongoContainer = "harmoniwatts-mongodb"
$SnapRoot = Join-Path $Root "docker\snapshots"
$PgDir = Join-Path $SnapRoot "postgres"
$MongoDir = Join-Path $SnapRoot "mongo\harmoniwatts"

if (-not (Test-Path (Join-Path $PgDir "harmoniwatts.dump"))) {
  throw "No hay docker\snapshots\postgres\harmoniwatts.dump"
}
if (-not (Test-Path $MongoDir)) {
  throw "No hay docker\snapshots\mongo\harmoniwatts\"
}

$confirm = Read-Host "Esto SOBRESCRIBE Postgres y Mongo actuales. Escribe SI para continuar"
if ($confirm -ne "SI") { Write-Host "Cancelado."; exit 0 }

$PgUser = "postgres"
$PgKeycloakDb = "keycloak_db"
$EnvFile = Join-Path $Root ".env"
if (Test-Path $EnvFile) {
  Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*POSTGRES_USER=(.+)$') { $PgUser = $Matches[1].Trim().Trim('"').Trim("'") }
    if ($_ -match '^\s*POSTGRES_DB=(.+)$') { $PgKeycloakDb = $Matches[1].Trim().Trim('"').Trim("'") }
  }
}

Write-Host "==> Restore Postgres ($PgKeycloakDb, harmoniwatts)"
docker cp (Join-Path $PgDir "keycloak_db.dump") "${PgContainer}:/tmp/keycloak_db.dump"
docker cp (Join-Path $PgDir "harmoniwatts.dump") "${PgContainer}:/tmp/harmoniwatts.dump"

$terminateSql = "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname IN ('$PgKeycloakDb', 'harmoniwatts') AND pid <> pg_backend_pid();"
docker exec $PgContainer psql -U $PgUser -d postgres -v ON_ERROR_STOP=1 -c $terminateSql

docker exec $PgContainer psql -U $PgUser -d postgres -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS $PgKeycloakDb;"
docker exec $PgContainer psql -U $PgUser -d postgres -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS harmoniwatts;"
docker exec $PgContainer psql -U $PgUser -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE $PgKeycloakDb;"
docker exec $PgContainer psql -U $PgUser -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE harmoniwatts;"

# pg_restore puede devolver 1 por warnings; no abortar el script entero
docker exec $PgContainer pg_restore -U $PgUser -d $PgKeycloakDb --no-owner --no-acl /tmp/keycloak_db.dump
docker exec $PgContainer pg_restore -U $PgUser -d harmoniwatts --no-owner --no-acl /tmp/harmoniwatts.dump
docker exec $PgContainer rm -f /tmp/keycloak_db.dump /tmp/harmoniwatts.dump

Write-Host "==> Restore Mongo (drop + mongorestore)"
docker exec $MongoContainer mongosh --quiet --eval "db.getSiblingDB('harmoniwatts').dropDatabase()"
docker exec $MongoContainer rm -rf /tmp/mongo-restore-harmoniwatts
docker cp $MongoDir "${MongoContainer}:/tmp/mongo-restore-harmoniwatts"
docker exec $MongoContainer mongorestore --db=harmoniwatts /tmp/mongo-restore-harmoniwatts
docker exec $MongoContainer rm -rf /tmp/mongo-restore-harmoniwatts

Write-Host "OK. Reinicia servicios:"
Write-Host "  docker compose restart keycloak harmoni-register harmoniwatts-vivienda-api harmoniwatts-electrodomesticos-api harmoniwatts-consumption-service harmoniwatts-insights-service"
