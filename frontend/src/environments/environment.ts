import type { DashboardApiEndpoints } from '../app/features/dashboard/dashboard.models';

/**
 * Build de producción (Kubernetes): frontend, APIs y Keycloak se sirven en el mismo dominio
 * detrás del Ingress (ver k8s/base/ingress.yaml). Se usa el origen absoluto (no rutas
 * relativas) porque el interceptor Bearer de `app.config.ts` compara URLs completas.
 */
const origin: string = globalThis.location?.origin ?? '';

export const environment = {
  production: true,
  keycloak: {
    url: `${origin}/auth`,
    realm: 'harmoniwatts',
    clientId: 'harmoniwatts-frontend',
  },
  registrationApiUrl: `${origin}/api/auth/register` as string | undefined,
  /** URL del backend para solicitar correo de restablecimiento de contraseña (harmoni-register). */
  forgotPasswordApiUrl: `${origin}/api/auth/forgot-password` as string | undefined,
  /**
   * Origen del API REST (sin barra final). Vacío = mismo origen que la app (`/api/...` en el host actual).
   * Debe coincidir con un patrón del interceptor Bearer en `app.config.ts`.
   */
  apiBaseUrl: origin as string,
  /** harmoni-register (Keycloak). Vacío = usar `apiBaseUrl` para perfil/contraseña. */
  harmoniRegisterBaseUrl: origin as string,
  /** API Spring Boot viviendas. Sin barra final. */
  viviendaApiBaseUrl: origin as string,
  /** tariff-service (tarifas por ubicación de la vivienda). Vacío = mismo origen. */
  tariffApiBaseUrl: origin as string,
  /** API Spring Boot electrodomésticos por vivienda. Sin barra final. */
  electrodomesticosApiBaseUrl: origin as string,
  /**
   * Base URL del insights-service (dashboard). Vacío: se usa `apiBaseUrl`.
   */
  dashboardInsightsBaseUrl: origin as string | undefined,
  /** Rutas versionadas del contrato DASHBOARD-API.md (sustituibles por entorno / despliegue). */
  dashboardApi: {
    summaryPath: '/api/v1/dashboard/summary',
    consumptionChartPath: '/api/v1/dashboard/consumption-chart',
    recommendationsPath: '/api/v1/dashboard/recommendations',
    appliancesTopPath: '/api/v1/dashboard/appliances/top',
    recommendationApplyPathTemplate: '/api/v1/recommendations/{id}/apply',
    recommendationDismissPathTemplate: '/api/v1/recommendations/{id}/dismiss',
  } satisfies DashboardApiEndpoints,
};
