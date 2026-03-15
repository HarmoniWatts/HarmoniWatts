# Keycloak + PostgreSQL con Docker Compose (HarmoniWatts)

Guía para levantar Keycloak con PostgreSQL usando Docker Compose (production-ready para autenticación con Angular u otras aplicaciones). Ejecutar los comandos **desde la carpeta HarmoniWatts** (donde está `docker-compose.yml`).

## Requisitos

- Docker y Docker Compose (v2+)
- Copiar `.env.example` a `.env` en esta carpeta y completar variables (al menos credenciales de BD y admin de Keycloak)

## Configuración inicial

```bash
# Desde la carpeta HarmoniWatts
cp .env.example .env
# Editar .env: POSTGRES_USER, POSTGRES_PASSWORD, KC_BOOTSTRAP_ADMIN_PASSWORD, etc.
```

## Comandos

Todos los comandos se ejecutan desde **HarmoniWatts** (raíz del repo o carpeta que contiene `docker-compose.yml`).

### Levantar los servicios

```bash
docker compose up -d
```

Con logs en tiempo real (sin `-d`):

```bash
docker compose up
```

### Ver logs en tiempo real

```bash
# Todos los servicios
docker compose logs -f

# Solo Keycloak
docker compose logs -f keycloak

# Solo PostgreSQL
docker compose logs -f postgres
```

### Detener servicios

```bash
docker compose down
```

### Detener y eliminar volúmenes (reset total)

**Cuidado:** borra la base de datos y los datos de Keycloak.

```bash
docker compose down -v
```

Luego volver a levantar con `docker compose up -d`.

---

## Verificación post-arranque

1. **Esperar a que Keycloak esté listo**  
   El primer arranque puede tardar 1–2 minutos. PostgreSQL debe estar *healthy* antes de que Keycloak arranque (`depends_on` con `service_healthy`).

2. **Admin Console de Keycloak**
   - URL: **http://localhost:8080** (o el puerto definido en `KEYCLOAK_HTTP_PORT` en `.env`)
   - Usuario: valor de `KC_BOOTSTRAP_ADMIN_USERNAME` (por defecto en `.env.example`: `admin`)
   - Contraseña: valor de `KC_BOOTSTRAP_ADMIN_PASSWORD`

3. **Comprobar que responde**
   - Navegador: http://localhost:8080 → debe cargar la página de Keycloak (login o bienvenida).
   - Health (si está habilitado): http://localhost:8080/health/ready

4. **Recomendado en producción**
   - Cambiar la contraseña del admin tras el primer login.
   - Crear un realm y un client para tu app Angular (por ejemplo con OIDC).
   - Configurar HTTPS y `KC_HOSTNAME` según [documentación de Keycloak](https://www.keycloak.org/server/configuration-production).

---

## Usuario admin temporal → administrador permanente

Si Keycloak muestra: *"You are logged in as a temporary admin user. To harden security, create a permanent admin account and delete the temporary one"*, haz lo siguiente **en el realm master** (donde entras por defecto):

### 1. Crear el usuario administrador permanente

1. En el menú lateral (realm **master**), ve a **Users**.
2. Clic en **Create new user**.
3. Rellena:
   - **Username:** el nombre de usuario que quieras para el admin (ej. `admin-permanent` o `keycloak-admin`).
   - **Email** y **First name / Last name** (opcional pero recomendado).
   - **Email verified:** ON si has puesto email.
4. Clic en **Create**.

### 2. Asignar contraseña al nuevo usuario

1. Entra en el usuario recién creado.
2. Ve a la pestaña **Credentials**.
3. **Set password:** introduce una contraseña segura y repítela.
4. Desactiva **Temporary** (para que no pida cambiar la contraseña en el próximo login).
5. **Save**.

### 3. Asignar roles de administrador (realm master)

1. Con el mismo usuario abierto, ve a la pestaña **Role mapping**.
2. Clic en **Assign role**.
3. En **Filter by realm roles** (o **Filter by clients**), asigna al menos:
   - **realm-management** → **realm-admin** (o los roles que necesites para administrar el realm).
   - Si aparece **master-realm** con un rol tipo **admin** o **manage-realm**, asígnalo también.
4. Asegúrate de que el usuario tenga capacidad de administrar el master y, si aplica, otros realms. Los roles típicos para “super admin” en master son los de **realm-management** (realm-admin, manage-users, etc.) y los de administración del realm master.
5. Cerrar el diálogo.

### 4. Comprobar el nuevo admin

1. Cierra sesión (desplegable arriba a la derecha → **Sign out**).
2. Vuelve a la Admin Console (http://localhost:8080).
3. Inicia sesión con el **nuevo** usuario y contraseña.
4. Comprueba que puedes entrar en **Users**, **Realm settings**, **Clients**, etc.

### 5. Eliminar el usuario admin temporal

1. Con el admin permanente ya logueado, ve a **Users**.
2. Busca el usuario que usabas antes (el de `KC_BOOTSTRAP_ADMIN_USERNAME`, por ejemplo `admin`).
3. Abre ese usuario y clic en **Delete** (o los tres puntos → Delete). Confirma.
4. A partir de ahí solo existirá el administrador permanente.

**Opcional:** deja de usar las variables de bootstrap en producción (quita o no definas `KC_BOOTSTRAP_ADMIN_USERNAME` / `KC_BOOTSTRAP_ADMIN_PASSWORD` en el `.env` o en el `docker-compose` una vez creado el admin permanente, para que no se recree el usuario temporal al reiniciar el contenedor; en algunas versiones Keycloak solo crea el temporal si no existe ningún admin).

### Si eliminaste el único admin y ya no puedes entrar

Si borraste el usuario admin (temporal o permanente) y no te queda ningún administrador, puedes **volver a crear un admin temporal** así:

1. En tu **`.env`** (carpeta HarmoniWatts), asegúrate de tener:
   - `KC_BOOTSTRAP_ADMIN_USERNAME=admin` (u otro nombre)
   - `KC_BOOTSTRAP_ADMIN_PASSWORD=una_contraseña_segura`
2. Reinicia solo el contenedor de Keycloak para que arranque de nuevo con bootstrap:
   ```bash
   docker compose up -d --force-recreate keycloak
   ```
3. Espera a que Keycloak levante (1–2 minutos) y entra en http://localhost:8080 con ese usuario y contraseña.
4. Vuelve a crear un **administrador permanente** (Users → Create new user, contraseña, roles) y, cuando lo tengas probado, ya puedes borrar de nuevo el usuario temporal si quieres.

No hace falta borrar volúmenes ni la base de datos; con recrear el contenedor y las variables de bootstrap suele bastar para que Keycloak cree de nuevo el usuario temporal.

### "You will need local access to create the administrative user"

Si Keycloak muestra este mensaje al intentar crear o usar el usuario admin, es porque **solo acepta crear el administrador desde un acceso "local"**.

**Solución recomendada:**

1. **Entra siempre por `http://localhost:8080`**  
   En el navegador usa exactamente **localhost**, no `127.0.0.1` ni la IP de tu máquina ni otro hostname. Keycloak considera "local" la petición cuando viene por localhost.
2. Si aun así no funciona, asegúrate de que el usuario admin se crea por **variables de bootstrap** al arrancar el contenedor (no por la consola). En tu `.env` deben estar `KC_BOOTSTRAP_ADMIN_USERNAME` y `KC_BOOTSTRAP_ADMIN_PASSWORD`; al hacer `docker compose up -d`, Keycloak crea ese usuario al iniciar y no pide "local access" para crearlo.
3. Si accedes a Keycloak desde **otra máquina** (servidor remoto, otra PC), la consola no te dejará crear el primer admin desde ahí. En ese caso el admin **tiene que existir ya** (creado con bootstrap al levantar el contenedor). No quites las variables de bootstrap en el `.env` y reinicia el contenedor para que cree el usuario; luego entra desde esa misma máquina usando la IP/hostname correspondiente y las credenciales del bootstrap.

**Resumen:** para crear el admin desde la interfaz, usa **http://localhost:8080** en la misma máquina donde corre Docker. Si no puedes usar localhost, el admin debe crearse con `KC_BOOTSTRAP_*` al arrancar el contenedor.

---

## Interfaz gráfica: pgAdmin

El stack incluye **pgAdmin** como interfaz web para administrar PostgreSQL.

1. **Acceso:** tras `docker compose up -d`, abre en el navegador **http://localhost:5050** (o el puerto definido en `PGADMIN_PORT` en `.env`).
2. **Login:** usa el email y contraseña de `PGADMIN_DEFAULT_EMAIL` y `PGADMIN_DEFAULT_PASSWORD` (por defecto `admin@example.com` / `admin`).
3. **Añadir el servidor PostgreSQL:**
   - Clic en "Add New Server".
   - **General** → Name: por ejemplo `Keycloak DB`.
   - **Connection:**
     - **Host:** `postgres` (nombre del servicio en Docker, no `localhost`).
     - **Port:** `5432`.
     - **Database:** valor de `POSTGRES_DB` (ej. `keycloak_db`).
     - **Username / Password:** valores de `POSTGRES_USER` y `POSTGRES_PASSWORD` de tu `.env`.
   - Guardar y ya puedes ver tablas, ejecutar SQL, etc.

En producción conviene no exponer pgAdmin o usar un proxy con autenticación.

---

## Conectar a PostgreSQL desde el host

Para inspeccionar la BD con DBeaver, TablePlus, psql, etc. (desde tu PC, no desde el contenedor):

| Parámetro   | Valor en `.env`        |
|------------|-------------------------|
| Host       | `localhost`             |
| Puerto     | `POSTGRES_PORT` (p. ej. 5432) |
| Base de datos | `POSTGRES_DB` (p. ej. `keycloak_db`) |
| Usuario    | `POSTGRES_USER`         |
| Contraseña | `POSTGRES_PASSWORD`     |

Ejemplo con `psql`:

```bash
psql -h localhost -p 5432 -U keycloak_user -d keycloak_db
```

(Usar el usuario y BD que hayas definido en `.env`.)

---

## Modo desarrollo vs producción

- **Desarrollo (actual):** el `command` del servicio `keycloak` es `start-dev`. Usa HTTP en el puerto 8080 y opciones pensadas para desarrollo.
- **Producción:** cambiar en `docker-compose.yml` el `command` del servicio `keycloak` a `start` (y, si aplica, usar imagen optimizada con `kc.sh build` y configurar `KC_HOSTNAME`, HTTPS y certificados según la [documentación de Keycloak en contenedores](https://www.keycloak.org/server/containers)).

---

## Configuración SMTP (correos de verificación / reset password)

**Tutorial completo:** ver **[KEYCLOAK-SMTP.md](KEYCLOAK-SMTP.md)** para el paso a paso de SMTP (Gmail, Mailtrap, parámetros, pruebas y resolución de problemas).

Resumen: configurar en **Realm settings → Email** (Host, Port, From, usuario y contraseña). Gmail: usar contraseña de aplicación con 2FA. Mailtrap: ideal para desarrollo. Las variables `KC_SPI_EMAIL_SMTP_*` en `.env` son opcionales; la configuración por consola es la más fiable.

---

## Estructura de archivos (en HarmoniWatts)

- `docker-compose.yml`: orquestación Keycloak + PostgreSQL, volúmenes nombrados, `depends_on` con healthcheck de PostgreSQL.
- `.env`: variables y secretos (no versionar; está en `.gitignore`).
- `.env.example`: plantilla sin valores reales para que el equipo copie a `.env`.
