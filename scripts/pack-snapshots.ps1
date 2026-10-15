#Requires -Version 5.1
<#
.SYNOPSIS
  Empaqueta docker/snapshots/ en un ZIP listo para copiar a otra PC.
#>
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$SnapRoot = Join-Path $Root "docker\snapshots"
$PgDump = Join-Path $SnapRoot "postgres\harmoniwatts.dump"
$KcDump = Join-Path $SnapRoot "postgres\keycloak_db.dump"
$MongoDir = Join-Path $SnapRoot "mongo\harmoniwatts"

if (-not (Test-Path $PgDump) -or -not (Test-Path $KcDump)) {
  throw "Faltan dumps de Postgres. Ejecuta antes: .\scripts\export-snapshots.ps1"
}
if (-not (Test-Path $MongoDir)) {
  throw "Falta dump de Mongo. Ejecuta antes: .\scripts\export-snapshots.ps1"
}

$stamp = Get-Date -Format "yyyyMMdd-HHmm"
$zipName = "harmoniwatts-snapshots-$stamp.zip"
$zipPath = Join-Path $Root $zipName

if (Test-Path $zipPath) { Remove-Item -Force $zipPath }

# Comprimir carpeta snapshots (incluye MANIFEST)
Compress-Archive -Path (Join-Path $SnapRoot "*") -DestinationPath $zipPath -CompressionLevel Optimal

Write-Host "ZIP creado: $zipPath"
Write-Host "Llévalo a la otra PC junto con el archivo .env (credenciales iguales)."
Write-Host "Allí: descomprime el contenido DENTRO de docker\snapshots\ y luego docker compose down -v && docker compose up -d --build"
