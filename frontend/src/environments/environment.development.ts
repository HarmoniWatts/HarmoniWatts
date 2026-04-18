import type { DashboardApiEndpoints } from '../app/features/dashboard/dashboard.models';

export const environment = {
  production: false,
  keycloak: {
    url: 'http://localhost:8080',
    realm: 'harmoniwatts',
    clientId: 'harmoniwatts-frontend',
  },
  /** Endpoint del backend que crea el usuario en Keycloak. Ver docs/REGISTER-API.md. */
  registrationApiUrl: 'http://localhost:8081/api/auth/register' as string | undefined,
  /** Endpoint para solicitar correo de restablecimiento de contraseña (harmoni-register). */
  forgotPasswordApiUrl: 'http://localhost:8081/api/auth/forgot-password' as string | undefined,
  /** harmoni-register: registro, olvidé contraseña, perfil y cambio de clave (Keycloak). */
  harmoniRegisterBaseUrl: 'http://localhost:8081',
  /** Mismo host que harmoni-register u otro gateway que exponga `/api/v1/dashboard/...`. */
  apiBaseUrl: 'http://localhost:8081',
  /** harmoniwatts-vivienda-api (Spring Boot — solo CRUD viviendas). */
  viviendaApiBaseUrl: 'http://localhost:8082',
  defaultHouseholdId: undefined as string | undefined,
  dashboardApi: {
    summaryPath: '/api/v1/dashboard/summary',
    consumptionChartPath: '/api/v1/dashboard/consumption-chart',
    recommendationsPath: '/api/v1/dashboard/recommendations',
    appliancesTopPath: '/api/v1/dashboard/appliances/top',
    recommendationApplyPathTemplate: '/api/v1/recommendations/{id}/apply',
    recommendationDismissPathTemplate: '/api/v1/recommendations/{id}/dismiss',
  } satisfies DashboardApiEndpoints,
};
