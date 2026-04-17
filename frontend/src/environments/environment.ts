import type { DashboardApiEndpoints } from '../app/features/dashboard/dashboard.models';

export const environment = {
  production: true,
  keycloak: {
    url: 'http://localhost:8080',
    realm: 'harmoniwatts',
    clientId: 'harmoniwatts-frontend',
  },
  registrationApiUrl: '' as string | undefined,
  /** URL del backend para solicitar correo de restablecimiento de contraseña (harmoni-register). */
  forgotPasswordApiUrl: '' as string | undefined,
  /**
   * Origen del API REST (sin barra final). Vacío = mismo origen que la app (`/api/...` en el host actual).
   * Debe coincidir con un patrón del interceptor Bearer en `app.config.ts`.
   */
  apiBaseUrl: '' as string,
  /** API Spring Boot (viviendas, etc.). Sin barra final. */
  viviendaApiBaseUrl: '' as string,
  /** Si el usuario tiene varias viviendas, se envía como `householdId` en las peticiones del dashboard. */
  defaultHouseholdId: undefined as string | undefined,
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
