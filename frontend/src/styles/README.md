# Sistema de tokens y temas (frontend)

Fuente única de verdad para los colores de la aplicación. Cualquier color
nuevo debe añadirse aquí; los componentes consumen siempre vía `var(--token)`.

## Capas

1. **Primitivos** (no usar directamente en componentes):
   `--hw-slate-*`, `--hw-cyan-*`, `--hw-green-*`, `--hw-amber-*`, etc.

2. **Semánticos** (los que se usan en CSS de componentes):
   - Fondos / superficies: `--color-bg`, `--color-bg-solid`,
     `--color-surface-1/2/3`, `--color-surface-elev*`, `--color-surface-panel`,
     `--color-surface-input`, `--color-surface-sidebar`.
   - Texto: `--color-text`, `--color-text-strong`, `--color-text-muted`,
     `--color-text-subtle`, `--color-text-on-accent`.
   - Bordes: `--color-border`, `--color-border-soft`, `--color-border-strong`,
     `--color-border-input`, `--color-border-divider`.
   - Acento (marca): `--color-accent`, `--color-accent-strong`,
     `--color-accent-soft`, `--color-accent-soft-hover`,
     `--color-accent-end`, `--color-accent-glow`, `--color-accent-ring`,
     `--color-accent-border`.
   - Estados: `--color-success`, `--color-warning`, `--color-danger`
     (con variantes `*-soft`, `*-text`).
   - Tarifas (dominio): `--color-tariff-{valle,llano,punta}-{bg,fg}`.
   - Gráficos: `--color-chart-{real,pred,grid,axis,current}`.
   - Auth: `--color-auth-bg`, `--color-auth-grid`, `--color-auth-shimmer`,
     `--color-auth-focus-1..4`.
   - Sombras: `--shadow-card`, `--shadow-card-strong`, `--shadow-panel`.

## Cómo cambiar el tema

El tema se conmuta con el atributo `data-theme="dark|light"` en `<html>`.
La inicialización ocurre en dos lugares:

- **`index.html`** (script inline): aplica el tema antes de Angular para
  evitar el "flash" de tema incorrecto. Lee `localStorage['harmoniwatts.theme']`
  y, si no existe, usa la preferencia del sistema (`prefers-color-scheme`).
- **`ThemeService`** (`src/app/core/theme/theme.service.ts`): puerto Angular.
  Expone signal `theme()`, métodos `set()` y `toggle()`. Persiste en
  `localStorage` y actualiza el atributo en `<html>`.

El componente `app-theme-toggle`
(`src/app/shared/components/theme-toggle`) consume el servicio y muestra el
botón sol/luna en:

- la franja superior del sidebar (`dash-shell`), variante icono;
- las pantallas de auth (`login`, `register`, `forgot-password`),
  variante flotante en la esquina superior derecha (`[floating]="true"`).

## Reglas para añadir colores

- ¿Nuevo color usado por un solo componente y sin variación entre temas?
  Si es derivado de un primitivo, úsalo directo (`var(--hw-...)`). Si tiene
  significado nuevo, créalo como semántico en `tokens.css`.
- ¿Color con variación entre tema oscuro y claro?
  Defínelo como semántico en ambos bloques (`:root[data-theme='dark']` y
  `:root[data-theme='light']`).
- Evita `#hex` o `rgba()` literales en el CSS de componentes; rómpe la
  consistencia entre temas y dificulta el mantenimiento.

## Cierre de sesión

El botón "Cerrar sesión" vive en `dash-shell.component.html` y llama a
`Keycloak.logout({ redirectUri: '/auth/login' })`. La sesión SSO queda
invalidada en el navegador y se redirige al login. Hay confirmación
mediante `window.confirm()` para evitar cierres accidentales.

La gestión de tokens (acceso/refresh) la realiza `keycloak-angular`:

- `provideKeycloak({ initOptions: { onLoad: 'check-sso', pkceMethod: 'S256' } })`
  en `app.config.ts`.
- `withAutoRefreshToken({ onInactivityTimeout: 'logout', sessionTimeout: 5*60*1000 })`
  renueva el access token de forma transparente y cierra la sesión por
  inactividad.
- `dash-shell.component.ts` además fuerza un `updateToken(60)` en cada
  navegación y al volver a la pestaña activa.
