# Snapshots / backup-restore de datos (Postgres + Mongo + Keycloak)

Guía para **clonar el estado real** de HarmoniWatts (inserciones, usuarios Keycloak, consumos Mongo) en otra PC, sin depender solo de `sql/init-*.sql` ni del JSON de demo de Mongo.

## Por qué hace falta

| Origen actual | Qué trae | Limitación |
|---------------|----------|------------|
| `sql/init-harmoniwatts.sql` + migrates | Schema + catálogos | **No** trae viviendas/electrodomésticos/datos que creaste en runtime |
| `BD/datos/….json` + `shift-timestamps.js` | Consumos de demo | **No** es el Mongo vivo; además mueve fechas |
| `keycloak-realm/*.json` | Config del realm (clientes, roles…) | Export parcial típico **sin usuarios** |
| Volúmenes Docker | Estado real | No se copian al clonar el repo |

Los **snapshots** (`pg_dump` + `mongodump`) sí son una copia del estado vivo.

## Qué se exporta

| Dump | Contiene |
|------|----------|
| `docker/snapshots/postgres/keycloak_db.dump` | Toda la BD de Keycloak: realm, **usuarios**, credenciales hasheadas, clients, IdP, roles… |
| `docker/snapshots/postgres/harmoniwatts.dump` | Datos de negocio (viviendas, electrodomésticos, tarifas, etc.) |
| `docker/snapshots/mongo/harmoniwatts/` | Colecciones Mongo (p. ej. `consumos_enriquecidos`) tal cual están |

Con el dump de `keycloak_db`, **Keycloak no requiere reconfiguración manual** en la PC destino (ni re-crear usuarios). El `realm-export.json` queda como respaldo de configuración si algún día levantas **sin** dump.

### ¿Algo manual en Keycloak?

Solo en estos casos:

1. **No** llevas `keycloak_db.dump` → entonces sí: realm JSON + crear usuarios / Google IdP / SMTP a mano (como en `KEYCLOAK-REALM-CLIENT.md`).
2. Secrets de IdP (Google client secret) o SMTP que **nunca** guardaste en Keycloak en la PC origen.
3. Cambias hostname/puertos y hay que revisar Valid Redirect URIs (`http://localhost:4200/*`, etc.).

Si restauras el dump completo y usas el **mismo `.env`**, normalmente entras con los mismos usuarios y el admin bootstrap que ya existía en esa BD.

## PC origen — exportar

1. Levanta el stack: `docker compose up -d`
2. Desde la raíz `HarmoniWatts`:

```powershell
.\scripts\export-snapshots.ps1
.\scripts\pack-snapshots.ps1
```

(Linux/macOS: `./scripts/export-snapshots.sh`)

3. Copia a la otra PC:
   - el ZIP `harmoniwatts-snapshots-*.zip`
   - tu archivo **`.env`** (mismas `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, admin Keycloak si lo usas)

## PC destino — montar

1. Clona/copia el repo HarmoniWatts.
2. Pon el `.env` en la raíz.
3. Descomprime el ZIP **dentro** de `docker/snapshots/` de modo que quede:

```text
docker/snapshots/MANIFEST.txt
docker/snapshots/postgres/keycloak_db.dump
docker/snapshots/postgres/harmoniwatts.dump
docker/snapshots/mongo/harmoniwatts/   (varios .bson)
```

4. Arranque limpio (borra volúmenes viejos si los hubiera):

```powershell
docker compose down -v
docker compose up -d --build
```

En el **primer** arranque con volumen Postgres vacío:

- `02-harmoniwatts-db.sh` crea la BD `harmoniwatts`
- `03-restore-snapshots.sh` restaura ambos `.dump`

El servicio `harmoniwatts-mongo-seed`:

- Si existe `docker/snapshots/mongo/harmoniwatts/` → `mongorestore` (**sin** desplazar fechas)
- Si no hay snapshot → cae al JSON de demo + `shift-timestamps.js` (comportamiento anterior)

5. Abre Keycloak (`http://localhost:8080`) y el frontend (`http://localhost:4200`) y verifica login + datos.

## Restore sobre un stack ya corriendo

Si no quieres `down -v` (o los init scripts ya no corren porque el volumen existe):

```powershell
.\scripts\restore-snapshots-runtime.ps1
```

Pide confirmación `SI` y sobrescribe Postgres + Mongo en caliente; luego reinicia Keycloak/APIs.

## Consistencia entre sistemas

Los `id_usuario` (UUID de Keycloak `sub`) y `id_vivienda` deben coincidir entre Keycloak, Postgres y Mongo. Por eso conviene exportar **las tres piezas juntas** y restaurarlas del mismo snapshot.

## Qué no cubre este flujo

- Imágenes Docker cacheadas: en destino hace falta build/pull normal.
- Secretos de nube (`GEMINI_API_KEY`, `OPENAI_API_KEY`, etc.): van en `.env`, no en los dumps. Ver `docs/VISION-PROVIDERS.md`.

## Comprobaciones rápidas

```powershell
# Postgres negocio
docker exec -it keycloak-postgres psql -U $env:POSTGRES_USER -d harmoniwatts -c "\dt"

# Keycloak users (tabla interna; solo para contar)
docker exec -it keycloak-postgres psql -U $env:POSTGRES_USER -d keycloak_db -c "SELECT count(*) FROM user_entity;"

# Mongo
docker exec -it harmoniwatts-mongodb mongosh --quiet --eval "db.getSiblingDB('harmoniwatts').consumos_enriquecidos.countDocuments()"
```

(Ajusta `POSTGRES_USER` / nombre de BD Keycloak según tu `.env`.)
