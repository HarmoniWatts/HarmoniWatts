# Flujo de autenticación (HarmoniWatts + Keycloak)

Descripción del flujo completo de autenticación: login, registro, verificación de correo y Google OAuth2/OIDC.

---

## Diagrama de flujo (paso a paso)

### 1. Login (usuario y contraseña)

```
Usuario → Angular (/auth/login) → Clic "Iniciar sesión"
    → keycloak.login() → Redirección a Keycloak (/realms/harmoniwatts/protocol/openid-connect/auth)
    → Usuario introduce usuario/contraseña en Keycloak
    → Keycloak valida (y verifica email si aplica)
    → Redirección a redirectUri (ej. http://localhost:4200/dashboard) con ?code=...
    → keycloak-js intercambia code por tokens (access_token, refresh_token)
    → Angular navega a /dashboard; AuthGuard permite acceso
```

- **Manejo de errores en Keycloak:** credenciales inválidas, usuario no verificado o cuenta bloqueada se muestran en la página de login de Keycloak. El usuario vuelve a la app solo cuando el login es correcto.

### 2. Registro

```
Usuario → Angular (/auth/register) → Clic "Registrarse"
    → keycloak.register() → Redirección a Keycloak (página de registro)
    → Usuario rellena nombre, email, contraseña (Keycloak aplica política de contraseñas)
    → Keycloak crea usuario y, si "Verify email" está ON, envía correo
    → Redirección a post-registro (ej. /auth/login)
    → Mensaje en app: "Revisa tu correo para verificar; no podrás iniciar sesión hasta verificarlo"
```

- **Validaciones en Keycloak:** correo no duplicado, política de contraseña (mín. 8 caracteres, mayúscula, número). En frontend se puede documentar o mostrar las mismas reglas antes de redirigir.

### 3. Verificación de correo

```
Usuario se registra → Keycloak envía email (SMTP configurado en Realm → Email)
    → Usuario abre enlace de verificación en el correo
    → Keycloak marca email como verificado
    → Usuario intenta login → Keycloak permite acceso
```

- Sin verificación, Keycloak puede bloquear el login hasta que el usuario verifique (según configuración del realm).

### 4. Login con Google (OAuth2 / OIDC)

```
Usuario → Angular → Clic "Iniciar sesión con Google"
    → keycloak.login({ idpHint: 'google' })
    → Redirección a Keycloak → Keycloak redirige a Google
    → Usuario autoriza en Google
    → Google redirige a Keycloak (broker/google/endpoint)
    → Keycloak: si email ya existe en el realm → vincula cuenta; si no → crea usuario (first login)
    → Keycloak redirige a la app (redirectUri) con tokens
    → Angular recibe tokens y el usuario queda logueado
```

- **Mapeo de atributos:** nombre, correo y (opcional) foto se mapean desde Google mediante los mappers del IdP en Keycloak.

---

## Ciclo de vida del token en Angular

1. **Inicialización (check-sso):** al cargar la app, keycloak-angular hace un “silent check” (iframe) para ver si hay sesión en Keycloak; si hay, obtiene tokens sin redirigir toda la página.
2. **Peticiones HTTP:** el interceptor `includeBearerTokenInterceptor` añade `Authorization: Bearer <access_token>` a las peticiones que coincidan con la URL de Keycloak (o las que configures).
3. **Refresh automático:** `withAutoRefreshToken` refresca el access token antes de que expire; si hay inactividad (sessionTimeout), puede hacer logout.
4. **Rutas protegidas:** `authGuard` comprueba si el usuario está logueado; si no, llama a `keycloak.login()` y redirige a Keycloak. Tras login exitoso, Keycloak redirige de vuelta y el guard permite el acceso.

---

## Criterios de aceptación (checklist)

| Criterio | Cómo se cumple |
|----------|----------------|
| Usuario se registra, recibe correo de verificación y solo accede tras verificarlo | Realm: Verify email ON; SMTP configurado en Keycloak; flujo de registro con envío de correo. |
| Políticas de contraseña en frontend y Keycloak | Keycloak: Password policy (mín. 8, mayúscula, dígito). Frontend: mensaje informativo antes de redirigir al registro. |
| Login con Google vincula cuentas existentes por correo | IdP Google configurado; First login flow con account linking (o por defecto según versión). |
| Rutas protegidas redirigen al login si token inválido o inexistente | `authGuard` usa `keycloak.isLoggedIn()`; si false, llama `keycloak.login()`. |
| Token se refresca automáticamente antes de expirar | `provideKeycloak` con `withAutoRefreshToken` en `app.config.ts`. |

---

## Referencia rápida de archivos

| Archivo | Función |
|---------|--------|
| `frontend/src/app/app.config.ts` | provideKeycloak, initOptions, withAutoRefreshToken, interceptor Bearer. |
| `frontend/src/app/app.routes.ts` | Rutas; `/dashboard` con `authGuard`. |
| `frontend/src/app/core/guards/auth.guard.ts` | Protege rutas; redirige a login si no autenticado. |
| `frontend/src/app/features/auth/login/*` | Página de login (redirección a Keycloak y a Google). |
| `frontend/src/app/features/auth/register/*` | Página de registro (redirección a Keycloak). |
| `docs/KEYCLOAK-REALM-CLIENT.md` | Pasos para crear realm, cliente y IdP Google. |
| `docs/DOCKER-KEYCLOAK.md` | Docker Compose, SMTP, pgAdmin. |
