# API de registro de usuarios (backend → Keycloak)

El frontend Angular incluye un formulario de registro (“Crear Cuenta”) que envía los datos a un **endpoint de tu backend**. El backend debe crear el usuario en Keycloak usando la **Admin REST API** de Keycloak. **No** se redirige a la página de registro de Keycloak; el registro se hace con el formulario.

## ¿Keycloak expone endpoints para crear usuarios?

**Sí**, pero de dos formas distintas:

1. **Admin REST API** (la que usamos desde el backend):
   - **Endpoint:** `POST /admin/realms/{realm}/users` (y luego `PUT .../users/{id}/reset-password` para la contraseña).
   - **Documentación:** [Keycloak Admin REST API - Users](https://www.keycloak.org/docs-api/latest/rest-api/index.html#_users_resource).
   - **Requisito:** hay que enviar un **Bearer token de administrador** (obtenido con usuario/contraseña de admin o con un cliente de servicio). Por eso no puede llamarse desde el frontend: las credenciales de admin no deben estar en el navegador. Un **backend** (como `backend-register`) obtiene el token y llama a la Admin API.

2. **Auto-registro (redirect):**
   - Keycloak ofrece una **página de registro** propia. Si en el realm está activado “User registration”, puedes redirigir al usuario a algo como:  
     `http://localhost:8080/realms/harmoniwatts/protocol/openid-connect/registrations`.
   - No hay un endpoint público tipo “POST JSON y crea usuario” para este flujo; es un flujo por redirección (el usuario rellena el formulario en Keycloak).

**Resumen:** Para registrar usuarios **desde tu propio formulario** (sin redirigir a Keycloak), se usa la **Admin REST API** desde un backend que tenga credenciales de admin; por eso existe `backend-register` en este proyecto.

### Por qué no hacerlo desde el frontend

No se recomienda llamar a la Admin API de Keycloak directamente desde el frontend (Angular en el navegador) por:

1. **Seguridad:** Para obtener el token de admin hay que usar usuario y contraseña de Keycloak. Esas credenciales quedarían en el código o en variables de entorno del frontend, que **cualquiera puede ver** (código fuente, herramientas de desarrollo, build). Con eso un atacante podría crear/borrar usuarios o tomar el control del realm.
2. **Buenas prácticas:** Las credenciales con privilegios de administración deben vivir solo en el **servidor** (backend). El frontend solo debe hablar con tu backend; el backend es quien se autentica ante Keycloak y llama a la Admin API.
3. **CORS:** Keycloak por defecto no permite peticiones al Admin API desde orígenes distintos (p. ej. `localhost:4200`), así que tendrías que tocar la configuración de Keycloak o usar proxies, añadiendo complejidad sin ganar seguridad.

Por eso el flujo correcto es: **frontend → tu endpoint (backend-register o tu API) → Keycloak Admin API**.

## Microservicio de registro (harmoni-register)

En el proyecto hay un **microservicio** dedicado al registro de usuarios:

1. **Local:** `cd harmoni-register && npm install && npm start`.
2. Keycloak en marcha (p. ej. `docker compose up -d`). Frontend: `registrationApiUrl: 'http://localhost:8081/api/auth/register'`.
3. En desarrollo, `environment.development.ts` ya tiene `registrationApiUrl: 'http://localhost:8081/api/auth/register'`.
4. Al enviar “Crear mi cuenta”, el formulario hace POST a ese endpoint y el usuario se crea en Keycloak sin redirección.

Variables del micro: `KEYCLOAK_URL`, `KEYCLOAK_REALM`, `KEYCLOAK_ADMIN_USERNAME`, `KEYCLOAK_ADMIN_PASSWORD`, `PORT`. Ver `harmoni-register/README.md`.

### Olvidé mi contraseña (vista propia)

La app incluye una vista personalizada en `/auth/forgot-password` (no redirige a Keycloak). El usuario escribe su correo y el frontend llama a `POST /api/auth/forgot-password` (harmoni-register). El microservicio busca el usuario en Keycloak por email y, si existe, envía el correo de restablecimiento con la Admin API (`execute-actions-email` con acción `UPDATE_PASSWORD`). Por seguridad, la respuesta es siempre 200 aunque el usuario no exista. Configura `forgotPasswordApiUrl` en el environment (p. ej. `http://localhost:8081/api/auth/forgot-password`). Para que el correo llegue, Keycloak debe tener SMTP configurado (ver `docs/KEYCLOAK-SMTP.md`).

## Configuración en el frontend

En `frontend/src/environments/environment.ts` (y `environment.development.ts`) define la URL del backend:

```ts
registrationApiUrl: 'http://localhost:8081/api/auth/register'
```

Si `registrationApiUrl` está vacía o no definida, el formulario muestra un mensaje indicando que hay que configurar el backend y no redirige a Keycloak. Opcionalmente el usuario puede usar el enlace “Registrarse en la página de Keycloak” para ir a Keycloak.

## Payload que envía el frontend

El frontend hace un **POST** (JSON) con este cuerpo:

| Campo        | Tipo   | Descripción                          |
|-------------|--------|--------------------------------------|
| `firstName` | string | Nombre                               |
| `lastName`  | string | Apellido                             |
| `email`     | string | Correo electrónico                   |
| `username`  | string | Igual que `email` (para Keycloak)   |
| `city`      | string | Ciudad (opcional)                    |
| `password`  | string | Contraseña en claro                  |

Ejemplo:

```json
{
  "firstName": "María",
  "lastName": "García",
  "email": "maria@example.com",
  "username": "maria@example.com",
  "city": "Bogotá",
  "password": "MiClave123"
}
```

## Qué debe hacer el backend

1. **Validar** el payload (campos obligatorios, formato de email, política de contraseña).
2. **Crear el usuario en Keycloak** con la [Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html):
   - `POST /admin/realms/{realm}/users`
   - Cuerpo mínimo: `username`, `email`, `firstName`, `lastName`, `enabled: true`, atributos si quieres guardar `city`, etc.
   - Luego asignar contraseña con `PUT /admin/realms/{realm}/users/{userId}/reset-password` (credenciales temporales: `false` si no quieres forzar cambio en el primer login).
3. Si tienes **Verify email** activado en el realm, opcionalmente disparar el envío del correo de verificación con la acción `VERIFY_EMAIL` (p. ej. con el endpoint de gestión de usuarios de Keycloak o enviando el usuario a “Required Actions”).
4. Responder **200** (o 201) en caso de éxito y **4xx** con un mensaje claro en caso de error (p. ej. “El correo ya está registrado”). El frontend muestra `error?.message` o el cuerpo de error.

## Seguridad

- El endpoint de registro debe ser **público** (no requiere token).
- El backend debe usar un **usuario de servicio** (service account) de Keycloak con roles de administración (p. ej. `realm-management` / `manage-users`) para llamar a la Admin API; **nunca** expongas el usuario/contraseña de admin de Keycloak en el frontend.
- Aplica rate limiting y, si es posible, CAPTCHA en el backend para evitar abusos.

## Resumen

| Elemento        | Valor                                                |
|-----------------|------------------------------------------------------|
| Método          | POST                                                 |
| Content-Type    | application/json                                     |
| URL (ejemplo)   | `http://localhost:8081/api/auth/register`            |
| Respuesta éxito | 200/201                                              |
| Respuesta error | 4xx con cuerpo que pueda incluir `message`           |

Con esto, el formulario de “Crear Cuenta” envía los datos al backend y el backend los persiste en Keycloak como usuarios del realm configurado (p. ej. `harmoniwatts`).
