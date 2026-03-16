# Configuración de Keycloak: Realm y Cliente (HarmoniWatts)

Esta guía detalla los pasos en **Keycloak Admin Console** para crear el realm, el cliente (frontend Angular) y el Identity Provider de Google, así como políticas de contraseña y verificación de correo.

**Realm listo sin configurar a mano:** si en la carpeta **`keycloak-realm/`** del proyecto hay un archivo JSON exportado del realm (p. ej. `harmoniwatts-realm.json`), Keycloak lo importa al arrancar con `docker compose up`. En ese caso no necesitas seguir esta guía paso a paso; solo revisar o ajustar en Admin Console si hace falta. Ver `keycloak-realm/README.md` y `DOCKER-KEYCLOAK.md`.

---

## Requisitos previos

- Keycloak en marcha (por ejemplo con `docker compose up -d` desde la raíz de HarmoniWatts).
- Acceso a Admin Console: **http://localhost:8080** con usuario y contraseña de administrador (definidos en `.env`: `KC_BOOTSTRAP_ADMIN_USERNAME` / `KC_BOOTSTRAP_ADMIN_PASSWORD`).

---

## 1. Crear el Realm

1. En la barra lateral izquierda, abrir el desplegable del **realm** (por defecto muestra **master**).
2. Clic en **Create realm**.
3. Completar:
   - **Realm name:** `harmoniwatts`
   - **Enabled:** ON
4. Clic en **Create**.

---

## 2. Política de contraseñas

1. En el menú del realm **harmoniwatts**, ir a **Realm settings**.
2. Pestaña **Security defenses** → sección **Password policy**.
3. Clic en **Add policy** y añadir:
   - **Minimum length:** `8`
   - **Uppercase characters:** `1`
   - **Digits:** `1`
4. Guardar con **Save**.

(Opcional: **Not username**, **Special characters** según necesidad.)

---

## 3. Login y registro (Realm settings → Login)

1. **Realm settings** → pestaña **Login**.
2. Activar **User registration** (Registration allowed), para que los usuarios puedan registrarse desde la app o desde la URL de registro de Keycloak. Si está en OFF, aparecerá "Registration not allowed".
3. Activar **Verify email** (Usuario debe verificar su correo electrónico) si quieres verificación por correo.
4. **Save**.

Para que Keycloak envíe el correo, configurar SMTP en **Realm settings** → **Email** (host, puerto, usuario, contraseña, From). Ver `KEYCLOAK-SMTP.md` y `DOCKER-KEYCLOAK.md`.

---

## 4. Crear el Cliente (Frontend Angular)

1. En el menú del realm **harmoniwatts**, ir a **Clients**.
2. **Create client**.

### 4.1 General settings

- **Client type:** `OpenID Connect`
- **Client ID:** `harmoniwatts-frontend`
- **Name** (opcional): `HarmoniWatts Frontend`
- **Description** (opcional): `Cliente SPA Angular`
- **Next**

### 4.2 Capability config

- **Client authentication:** OFF (cliente público, sin secret).
- **Authorization:** OFF.
- **Authentication flow:**
  - **Standard flow:** ON (Authorization Code; para Google y redirección).
  - **Direct access grants:** ON (necesario para que el login con usuario/contraseña en la app funcione sin redirigir a Keycloak).
  - **Implicit flow:** OFF.
- **Next**

### 4.3 Login settings

- **Root URL:** `http://localhost:4200` (URL base de tu app Angular en desarrollo).
- **Home URL:** `http://localhost:4200`
- **Valid redirect URIs:**
  - `http://localhost:4200/*`
  - En producción añadir, por ejemplo: `https://tu-dominio.com/*`
- **Valid post logout redirect URIs:**
  - `http://localhost:4200/*`
  - En producción: `https://tu-dominio.com/*`
- **Web origins:**
  - `http://localhost:4200`
  - En producción: `https://tu-dominio.com`
- **Save**.

### 4.4 Login en la app sin redirigir a Keycloak (Direct access grants)

Para que el formulario de login de la app Angular envíe usuario y contraseña directamente a Keycloak (sin redirección), el cliente debe tener **Direct access grants** activado:

1. **Clients** → **harmoniwatts-frontend** → pestaña **Capability config** (o **Settings** si ya creaste el cliente).
2. En **Authentication flow**, activar **Direct access grants** (Direct access grants enabled).
3. **Save**.

Si está en OFF, el login con correo/contraseña en la app fallará; Keycloak solo aceptará el flujo por redirección (Standard flow).

### Resumen cliente

| Campo                    | Valor                      |
|--------------------------|----------------------------|
| Client ID                | `harmoniwatts-frontend`    |
| Client type              | OpenID Connect (public)     |
| Standard flow            | ON                         |
| Direct access grants     | **ON** (login en app con user/password) |
| Root URL                 | `http://localhost:4200`    |
| Valid redirect URIs      | `http://localhost:4200/*`  |
| Valid post logout URIs   | `http://localhost:4200/*`  |
| Web origins              | `http://localhost:4200`    |

---

## 5. Identity Provider: Google (OAuth2 / OIDC)

### 5.1 Crear credenciales en Google Cloud

1. Ir a [Google Cloud Console](https://console.cloud.google.com/) → **APIs & Services** → **Credentials**.
2. **Create credentials** → **OAuth client ID**.
3. **Application type:** `Web application`.
4. **Name:** p. ej. `HarmoniWatts Keycloak`.
5. **Authorized redirect URIs:** añadir la URL de callback de Keycloak:
   - `http://localhost:8080/realms/harmoniwatts/broker/google/endpoint`
   - En producción: `https://tu-keycloak.com/realms/harmoniwatts/broker/google/endpoint`
6. Crear y copiar **Client ID** y **Client secret**.

### 5.2 Crear el Identity Provider en Keycloak

1. En el realm **harmoniwatts**, ir a **Identity providers**.
2. **Add provider** → elegir **Google**.
3. **Alias:** `google` (se usará como `idpHint` en el frontend).
4. **Display name:** `Google`.
5. **Enabled:** ON.
6. **Client ID:** (el de Google Cloud).
7. **Client secret:** (el de Google Cloud).
8. **Save**.

### 5.3 Mapeo de atributos (opcional)

En el IdP **google**, pestaña **Mappers**:

- Keycloak suele crear mappers por defecto para `email`, `firstName`, `lastName`, etc.
- Si quieres **foto de perfil**, crear un mapper:
  - **Mapper type:** Attribute Importer
  - **Social profile JSON field path:** `picture`
  - **User attribute name:** `picture` (o el que use tu app).

### 5.4 First login / vinculación

- **First login flow:** por defecto Keycloak puede crear el usuario automáticamente si no existe.
- Para **vincular cuentas** (mismo email): en **Identity providers** → **google** → **Settings** revisar **First login flow**; si usas “first broker login” con “Account linking”, los usuarios con el mismo email se pueden vincular.

---

## 6. Flujo de autenticación “Verify Email”

1. En **Realm settings** → **Authentication** → pestaña **Flows**.
2. Copiar el flujo **Browser** si quieres personalizarlo, o usar el por defecto.
3. En **Authentication** → **Policies** (o dentro del flujo), el paso **Verify Email** debe estar en el flujo de registro (p. ej. **Registration flow**).
4. Por defecto, si **Verify email** está activado en Realm settings, Keycloak enviará el correo tras el registro y el usuario no podrá iniciar sesión hasta verificar.

---

## 7. Roles (opcional)

1. **Realm roles** → **Create role**.
2. Ejemplos: `user`, `admin`, `viewer`.
3. Asignar roles a usuarios desde **Users** → usuario → **Role mapping**.

Para proteger rutas por rol en Angular, usar el guard con `data: { roles: ['admin'] }` y comprobar en el guard si el usuario tiene ese rol (keycloak-angular permite guards por rol).

---

## 8. Resumen de URLs y valores para el frontend

| Concepto        | Valor |
|----------------|--------|
| Keycloak URL   | `http://localhost:8080` |
| Realm          | `harmoniwatts` |
| Client ID      | `harmoniwatts-frontend` |
| Login redirect  | `http://localhost:4200/dashboard` |
| Post logout    | `http://localhost:4200/auth/login` |
| Olvidé contraseña | Vista propia `/auth/forgot-password` → POST a harmoni-register `/api/auth/forgot-password` → Keycloak envía correo (requiere SMTP; ver `docs/KEYCLOAK-SMTP.md`) |
| Google IdP     | Alias `google` → en app: `idpHint: 'google'` |

Estos valores deben coincidir con `environment.keycloak` en el proyecto Angular y con la configuración del cliente en Keycloak.

---

## 9. Comprobar que todo funciona

1. **Registro:** desde la app Angular, “Registrarse” → redirección a Keycloak → formulario de registro → correo de verificación (si SMTP está configurado).
2. **Login:** “Iniciar sesión” → Keycloak login → redirección a `/dashboard`.
3. **Olvidé contraseña:** en login, "¿Olvidaste tu contraseña?" → vista propia `/auth/forgot-password` → el usuario introduce su correo → harmoni-register envía el correo vía Keycloak (requiere SMTP).
4. **Google:** “Iniciar sesión con Google” → redirección a Google → vuelta a la app.
5. **Rutas protegidas:** acceder a `/dashboard` sin estar logueado debe redirigir al login de Keycloak.

Si algo falla, revisar en Keycloak **Events** (realm) y la pestaña **Network** del navegador (redirect URIs, CORS, respuestas 4xx).

---

## 10. (Opcional) Content Security Policy si usas silent check-sso

Si en el frontend usas `silentCheckSsoRedirectUri` (comprobación de sesión en iframe), el navegador puede bloquear con *"Framing 'http://localhost:8080/' violates Content Security Policy directive: frame-ancestors 'self'"*. Para permitirlo:

1. **Realm settings** → **Security defenses** → pestaña **Headers**.
2. En **Content-Security-Policy** (o **Default headers**), añadir en `frame-ancestors` el origen de la app, por ejemplo: `frame-ancestors 'self' http://localhost:4200`.
3. En producción, usar tu dominio real (ej. `https://tu-dominio.com`).

Sin este cambio, la app funciona usando `check-sso` sin iframe (redirect completo cuando hace falta comprobar sesión).

---

## 11. Cómo cambiar el diseño (temas) de Keycloak

Las pantallas de Keycloak (login, registro, olvidar contraseña, cuenta) usan **temas**. Puedes elegir un tema incorporado o uno personalizado para que coincida con HarmoniWatts (colores, logo, tipografía).

### 11.1 Elegir tema del realm (rápido)

1. **Realm settings** → pestaña **Themes** (o **General** según versión).
2. Configurar:
   - **Login theme:** tema para la pantalla de login de Keycloak (ej. `keycloak`, `keycloak.v2`, `base`).
   - **Account theme:** tema para la consola de cuenta de usuario (Account Console).
   - **Email theme:** tema para los correos que envía Keycloak (verificación, reset password).
   - **Admin theme:** solo afecta a la Admin Console (no a las pantallas que ven los usuarios finales).
3. **Save**.

Los temas incluidos (`keycloak`, `keycloak.v2`, `base`) no se pueden editar; solo cambias cuál está activo.

### 11.2 Crear un tema personalizado (login / registro a tu medida)

Para un diseño propio (logo HarmoniWatts, colores verde-azul, etc.) hay que **crear un tema** y desplegarlo en el servidor Keycloak.

#### Estructura de un tema de login

En el servidor (o en una imagen Docker que extienda la oficial), los temas viven en un directorio que Keycloak carga. Ejemplo de estructura para un tema `harmoniwatts`:

```
themes/
  harmoniwatts/
    login/
      theme.properties    ← nombre del tema, herencia (parent)
      resources/
        css/
          login.css        ← estilos
        img/
          logo.png        ← logo
      template.ftl        ← plantilla (FreeMarker); opcional si usas el base
```

- **theme.properties** (mínimo):

  ```properties
  parent=keycloak
  import=common/keycloak
  styles=css/login.css
  ```

- **login.css**: aquí defines colores de fondo, botones, inputs, etc. (por ejemplo los mismos que en tu app: `#0f172a`, `#22d3ee`, `#4ade80`).

- **Logo:** en `resources/img/logo.png` y referenciado en la plantilla o con las variables estándar de Keycloak.

#### Cómo aplicar el tema en Keycloak en Docker

1. **Crear la carpeta del tema** en tu proyecto (ej. `keycloak-themes/harmoniwatts/login/`).
2. Añadir `theme.properties`, `login.css` y, si quieres, una plantilla que extienda la de Keycloak (copiando la de `keycloak` o `keycloak.v2` y modificando).
3. **Montar el tema en el contenedor** en tu `docker-compose.yml`:

   ```yaml
   keycloak:
     image: quay.io/keycloak/keycloak:latest
     volumes:
       - ./keycloak-themes:/opt/keycloak/themes/custom
     environment:
       KC_SPI_THEME_DIR: /opt/keycloak/themes
       # Opcional: tema por defecto para el realm
       # KC_SPI_THEME_DEFAULT: harmoniwatts
       # KC_SPI_THEME_LOGIN_THEME: harmoniwatts
   ```

   La ruta exacta puede variar según versión (a veces es `/opt/keycloak/themes` y el tema se llama por la carpeta, ej. `custom/harmoniwatts/login`).

4. En **Realm settings** → **Themes**, poner **Login theme** = `harmoniwatts` (el nombre de la carpeta bajo tu volumen).

#### Documentación oficial de temas

- [Server Developer Guide - Themes](https://www.keycloak.org/docs/latest/server_development/#_themes): estructura, `theme.properties`, variables.
- [Creating a custom theme](https://www.keycloak.org/docs/latest/server_development/#creating-a-custom-theme): pasos para crear y registrar un tema.

Con un tema personalizado puedes hacer que login, registro y “olvidar contraseña” de Keycloak usen el mismo estilo que tu app Angular (HarmoniWatts).
