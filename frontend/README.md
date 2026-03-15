# HarmoniWatts – Frontend (Angular)

Aplicación Angular con autenticación Keycloak: login, registro, verificación de correo y login con Google (OAuth2/OIDC).

## Stack

- **Angular** 19+
- **keycloak-angular** + **keycloak-js** para Identity Provider
- Keycloak (realm `harmoniwatts`, cliente `harmoniwatts-frontend`)
- PostgreSQL (persistencia de Keycloak, no del frontend)

## Requisitos

- Node.js 20+
- Keycloak y PostgreSQL en marcha (desde la raíz del repo: `docker compose up -d`)
- Realm y cliente configurados en Keycloak según [KEYCLOAK-REALM-CLIENT.md](../docs/KEYCLOAK-REALM-CLIENT.md)

## Instalación

```bash
cd frontend
npm install
```

## Configuración

- **Keycloak:** en `src/environments/`:
  - `environment.development.ts`: desarrollo (por defecto en `app.config.ts`)
  - `environment.ts`: producción
- Ajustar `url`, `realm` y `clientId` si no usas `http://localhost:8080`, `harmoniwatts` y `harmoniwatts-frontend`.

## Desarrollo

```bash
npm start
```

Abre http://localhost:4200. Las rutas:

- `/` → redirige a `/auth/login`
- `/auth/login` → Iniciar sesión (redirección a Keycloak) y opción Google
- `/auth/register` → Registro (redirección a Keycloak)
- `/dashboard` → Área protegida (requiere login)

## Build

```bash
npm run build
```

Salida en `dist/harmoniwatts-frontend/`. Para producción, usar `environment.ts` (file replacement en `angular.json` si aplica).

## Estructura relevante

```
src/app/
├── app.config.ts          # Keycloak, interceptors, guards
├── app.routes.ts         # Rutas y authGuard en /dashboard
├── core/
│   └── guards/
│       └── auth.guard.ts # Protección de rutas
├── features/
│   ├── auth/
│   │   ├── auth.routes.ts
│   │   ├── login/        # Página de login
│   │   └── register/     # Página de registro
│   └── dashboard/        # Página protegida de ejemplo
└── environments/         # URL/realm/clientId de Keycloak
```

## Documentación

- **Reino y cliente Keycloak:** [docs/KEYCLOAK-REALM-CLIENT.md](../docs/KEYCLOAK-REALM-CLIENT.md)
- **Flujo de autenticación:** [docs/AUTH-FLOW.md](../docs/AUTH-FLOW.md)
- **Docker (Keycloak + PostgreSQL):** [docs/DOCKER-KEYCLOAK.md](../docs/DOCKER-KEYCLOAK.md)

## Notas

- El login y el registro se realizan en las páginas de Keycloak (redirección). Las validaciones de contraseña y correo se aplican en Keycloak (realm y cliente configurados según el markdown anterior).
- Para **KeycloakService:** si usas keycloak-angular 19+ y el servicio está deprecado, puedes inyectar el cliente Keycloak (keycloak-js) según la documentación de keycloak-angular.
- **silent-check-sso:** el archivo `public/silent-check-sso.html` es necesario para el flujo `check-sso` en la inicialización.
