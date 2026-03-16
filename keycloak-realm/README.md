# Importación del realm Keycloak al arrancar

Los archivos `.json` que coloques en esta carpeta se importan automáticamente cuando Keycloak arranca con `docker compose up` (si el realm no existe aún en la base de datos). Así, quien clone el proyecto puede tener el realm **harmoniwatts** ya configurado (clientes, políticas, IdP, etc.) sin repetir la configuración manual.

## Cómo generar el archivo de realm

1. Arranca Keycloak y configura el realm tal como indica [KEYCLOAK-REALM-CLIENT.md](../docs/KEYCLOAK-REALM-CLIENT.md) (realm `harmoniwatts`, cliente `harmoniwatts-frontend`, políticas, Google IdP si lo usas, etc.).
2. En la **Admin Console** de Keycloak (`http://localhost:8080`):
   - Selecciona el realm **harmoniwatts**.
   - Ve a **Realm settings**.
   - Pestaña **Action** (o menú de tres puntos) → **Partial export** (exportación parcial, sin usuarios) o **Export** (exportación completa; incluye usuarios si los hay).
3. Guarda el JSON descargado en esta carpeta con un nombre como `harmoniwatts-realm.json` (cualquier nombre `.json` vale).

## Qué incluir en el export

- **Partial export** (recomendado para compartir): incluye realm, clientes, roles, políticas, Identity Providers, etc. **No** incluye usuarios ni client secrets; los usuarios se crean por registro o por harmoni-register.
- Si usas **Export** completo, ten en cuenta que puede incluir usuarios y datos sensibles; no subas ese archivo al repositorio si hay información real.

## Primera ejecución

Al hacer `docker compose up -d` por primera vez (o con volúmenes nuevos):

1. PostgreSQL y Keycloak arrancan.
2. Keycloak monta esta carpeta en `/opt/keycloak/data/import` y ejecuta con `--import-realm`.
3. Todos los `.json` de esta carpeta se importan; el realm `harmoniwatts` queda creado con la configuración exportada.

Si ya tenías datos en los volúmenes de Docker (Keycloak o PostgreSQL), el realm puede existir de antes; en ese caso la importación no sobrescribe. Para empezar de cero: `docker compose down -v` (elimina volúmenes) y luego vuelve a subir.

## Archivos en esta carpeta

- `harmoniwatts-realm.json`: (opcional) exportación del realm. Si el mantenedor del proyecto lo añade al repositorio, quien clone ya tendrá el realm preconfigurado al hacer `docker compose up`.
