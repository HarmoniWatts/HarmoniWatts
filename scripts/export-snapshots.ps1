#Requires -Version 5.1
<#
.SYNOPSIS
  Exporta Postgres (keycloak_db + harmoniwatts) y Mongo (harmoniwatts) a docker/snapshots/

.DESCRIPTION
  Requiere contenedores en marcha: keycloak-postgres, harmoniwatts-mongodb.
  Uso (desde la raíz HarmoniWatts):
    .\scripts\export-snapshots.ps1
#>
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$PgContainer = "keycloak-postgres"
$MongoContainer = "harmoniwatts-mongodb"
$SnapRoot = Join-Path $Root "docker\snapshots"
$PgOut = Join-Path $SnapRoot "postgres"
$MongoOut = Join-Path $SnapRoot "mongo"

function Assert-ContainerRunning([string]$Name) {
  $id = docker ps -q -f "name=^/${Name}$"
  if (-not $id) {
    # nombre sin ancla estricta (Windows Docker a veces no usa /name)
    $id = docker ps --format "{{.Names}}" | Where-Object { $_ -eq $Name }
  }
  if (-not $id) {
    throw "Contenedor '$Name' no está en marcha. Ejecuta: docker compose up -d"
  }
}

Write-Host "==> Comprobando contenedores..."
Assert-ContainerRunning $PgContainer
Assert-ContainerRunning $MongoContainer

New-Item -ItemType Directory -Force -Path $PgOut | Out-Null
New-Item -ItemType Directory -Force -Path $MongoOut | Out-Null

# Cargar POSTGRES_* desde .env si existe
$PgUser = "postgres"
$PgKeycloakDb = "keycloak_db"
$EnvFile = Join-Path $Root ".env"
if (Test-Path $EnvFile) {
  Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*POSTGRES_USER=(.+)$') { $PgUser = $Matches[1].Trim().Trim('"').Trim("'") }
    if ($_ -match '^\s*POSTGRES_DB=(.+)$') { $PgKeycloakDb = $Matches[1].Trim().Trim('"').Trim("'") }
  }
}

Write-Host "==> Export Postgres: $PgKeycloakDb + harmoniwatts (usuario=$PgUser)"

docker exec $PgContainer pg_dump -U $PgUser -d $PgKeycloakDb -Fc -f /tmp/keycloak_db.dump
docker cp "${PgContainer}:/tmp/keycloak_db.dump" (Join-Path $PgOut "keycloak_db.dump")
docker exec $PgContainer rm -f /tmp/keycloak_db.dump

docker exec $PgContainer pg_dump -U $PgUser -d harmoniwatts -Fc -f /tmp/harmoniwatts.dump
docker cp "${PgContainer}:/tmp/harmoniwatts.dump" (Join-Path $PgOut "harmoniwatts.dump")
docker exec $PgContainer rm -f /tmp/harmoniwatts.dump

Write-Host "==> Export Mongo: harmoniwatts"
docker exec $MongoContainer rm -rf /tmp/mongo-dump
docker exec $MongoContainer mongodump --db=harmoniwatts --out=/tmp/mongo-dump

$MongoTarget = Join-Path $MongoOut "harmoniwatts"
if (Test-Path $MongoTarget) { Remove-Item -Recurse -Force $MongoTarget }
docker cp "${MongoContainer}:/tmp/mongo-dump/harmoniwatts" $MongoTarget
docker exec $MongoContainer rm -rf /tmp/mongo-dump

$stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss K"
$manifest = @"
HarmoniWatts data snapshot
exported_at: $stamp
postgres_container: $PgContainer
postgres_user: $PgUser
postgres_dumps:
  - $PgKeycloakDb.dump  (Keycloak: usuarios, realm, clients, IdP…)
  - harmoniwatts.dump   (negocio: viviendas, electrodomésticos, …)
mongo_container: $MongoContainer
mongo_dump: mongo/harmoniwatts/
notes:
  - Copia también el archivo .env (mismas POSTGRES_* / KC_*).
  - En destino: docker compose down -v && docker compose up -d --build
  - Keycloak NO requiere reconfiguración manual si keycloak_db.dump se restaura.
"@
Set-Content -Path (Join-Path $SnapRoot "MANIFEST.txt") -Value $manifest -Encoding UTF8

Write-Host ""
Write-Host "OK. Snapshots en: $SnapRoot"
Write-Host "Siguiente: .\scripts\pack-snapshots.ps1   (ZIP para otra PC)"
Get-ChildItem -Recurse $SnapRoot -File | Select-Object FullName, Length | Format-Table -AutoSize
