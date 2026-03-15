# Microservicio de registro de usuarios (HarmoniWatts)

Microservicio que expone un endpoint para el registro de usuarios. Recibe el payload del formulario del frontend Angular y crea el usuario en **Keycloak** usando la Admin REST API.

## Endpoints

| Método | Ruta                   | Descripción                          |
|--------|------------------------|--------------------------------------|
| POST   | `/api/auth/register`   | Registra un usuario en Keycloak      |
| GET    | `/health`              | Estado del servicio (ok)             |

## Requisitos

- **Node.js** >= 18
- **Keycloak** en marcha (realm creado, usuario admin disponible)

## Configuración

Variables de entorno (o archivo `.env` si usas `dotenv`; por defecto se leen de `process.env`):

| Variable                  | Descripción                    | Por defecto           |
|---------------------------|--------------------------------|------------------------|
| `PORT`                    | Puerto del microservicio       | `8081`                 |
| `KEYCLOAK_URL`            | URL base de Keycloak           | `http://localhost:8080`|
| `KEYCLOAK_REALM`          | Realm donde crear usuarios     | `harmoniwatts`         |
| `KEYCLOAK_ADMIN_USERNAME` | Usuario admin de Keycloak      | `admin`                |
| `KEYCLOAK_ADMIN_PASSWORD` | Contraseña del admin           | *(obligatoria)*        |

Puedes copiar `.env.example` a `.env` y ajustar. La contraseña debe coincidir con la del admin de Keycloak (p. ej. la de tu `docker-compose` / `.env` del proyecto: `KC_BOOTSTRAP_ADMIN_PASSWORD`).

## Uso

```bash
cd micro-register
npm install
npm start
```

En desarrollo con recarga al cambiar código:

```bash
npm run dev
```

El frontend debe tener en `environment.development.ts`:

```ts
registrationApiUrl: 'http://localhost:8081/api/auth/register'
```

## Payload de registro (POST /api/auth/register)

Cuerpo JSON:

| Campo       | Tipo   | Obligatorio | Descripción        |
|------------|--------|-------------|--------------------|
| firstName  | string | Sí          | Nombre             |
| lastName   | string | Sí          | Apellido           |
| email      | string | Sí          | Correo (válido)    |
| password   | string | Sí          | Mínimo 8 caracteres|
| username   | string | No          | Si no se envía = email |
| city       | string | No          | Ciudad             |

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

Respuesta éxito: `201` con `{ "success": true }`.  
Error: `400` con `{ "message": "..." }` (p. ej. "El correo o usuario ya está registrado.").

## Estructura

```
micro-register/
├── src/
│   ├── server.js   # Entrada, arranque del servidor
│   ├── app.js      # Express app, rutas y CORS
│   ├── config.js   # Variables de entorno
│   ├── keycloak.js # Cliente Keycloak (token + crear usuario)
│   └── routes.js   # Handlers de /api/auth/register y /health
├── .env.example
├── package.json
└── README.md
```

## Integración con el proyecto

- El **frontend** Angular envía el formulario "Crear Cuenta" a `registrationApiUrl` (este micro en `http://localhost:8081/api/auth/register`).
- Este micro obtiene token de admin de Keycloak, crea el usuario en el realm y le asigna la contraseña.
- No expongas `KEYCLOAK_ADMIN_PASSWORD` en el frontend; solo en este micro o en variables de entorno del servidor.
