# Snapshots de datos (Postgres + Mongo)

Copia del **estado vivo** de las bases para montar HarmoniWatts en otra PC sin depender solo de los scripts SQL/JSON de demo.

## Contenido esperado

```
docker/snapshots/
  MANIFEST.txt                 # generado por el export (fecha, contenedores, DBs)
  postgres/
    keycloak_db.dump           # Keycloak: realm, usuarios, roles, IdP, etc.
    harmoniwatts.dump          # negocio: viviendas, electrodomésticos, …
  mongo/
    harmoniwatts/              # mongodump (colecciones .bson + .metadata.json)
```

Los binarios (`.dump`, `.bson`) **no se versionan** en git (ver `.gitignore`). Compártelos por ZIP/USB/Drive.

## Flujo rápido

1. En la PC origen (stack arriba): `.\scripts\export-snapshots.ps1`
2. Empaqueta: `.\scripts\pack-snapshots.ps1` → genera `harmoniwatts-snapshots-YYYYMMDD.zip`
3. En la PC destino: copia el ZIP, descomprime en `docker/snapshots/`, copia `.env` (mismas credenciales Postgres), luego:
   ```bash
   docker compose down -v
   docker compose up -d --build
   ```
4. En el **primer** arranque con volúmenes vacíos, Postgres y el seed de Mongo restauran automáticamente desde estos snapshots.

Guía completa: [docs/SNAPSHOTS-BACKUP-RESTORE.md](../../docs/SNAPSHOTS-BACKUP-RESTORE.md)
