import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import {
  provideKeycloak,
  withAutoRefreshToken,
  AutoRefreshTokenService,
  UserActivityService,
  createInterceptorCondition,
  IncludeBearerTokenCondition,
  includeBearerTokenInterceptor,
  INCLUDE_BEARER_TOKEN_INTERCEPTOR_CONFIG,
} from 'keycloak-angular';

import { routes } from './app.routes';
import { environment } from '../environments/environment';

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

const keycloakUrl = environment.keycloak.url;

const keycloakBearerCondition = createInterceptorCondition<IncludeBearerTokenCondition>({
  urlPattern: new RegExp(`^${escapeRegExp(keycloakUrl)}(/.*)?$`, 'i'),
  bearerPrefix: 'Bearer',
});

const apiBase = (environment.apiBaseUrl ?? '').replace(/\/$/, '');
const apiBearerCondition = apiBase
  ? createInterceptorCondition<IncludeBearerTokenCondition>({
      urlPattern: new RegExp(`^${escapeRegExp(apiBase)}(/.*)?$`, 'i'),
      bearerPrefix: 'Bearer',
    })
  : createInterceptorCondition<IncludeBearerTokenCondition>({
      urlPattern: /^https?:\/\/[^/]+\/api\/v\d+\//i,
      bearerPrefix: 'Bearer',
    });

const viviendaBase = (environment.viviendaApiBaseUrl ?? '').replace(/\/$/, '');
const viviendaBearerCondition = viviendaBase
  ? createInterceptorCondition<IncludeBearerTokenCondition>({
      urlPattern: new RegExp(`^${escapeRegExp(viviendaBase)}(/.*)?$`, 'i'),
      bearerPrefix: 'Bearer',
    })
  : null;

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideHttpClient(withInterceptors([includeBearerTokenInterceptor])),
    {
      provide: INCLUDE_BEARER_TOKEN_INTERCEPTOR_CONFIG,
      useValue: [keycloakBearerCondition, apiBearerCondition, ...(viviendaBearerCondition ? [viviendaBearerCondition] : [])],
    },
    provideKeycloak({
      config: {
        url: environment.keycloak.url,
        realm: environment.keycloak.realm,
        clientId: environment.keycloak.clientId,
      },
      initOptions: {
        onLoad: 'check-sso',
        // Evita el iframe de comprobación de sesión (3rd-party cookies / CSP); sin esto,
        // `updateToken()` puede fallar en SPAs y las APIs reciben token inválido o sin Authorization.
        checkLoginIframe: false,
        // Sin silentCheckSsoRedirectUri para evitar iframe y error CSP "frame-ancestors 'self'".
        // Keycloak hará redirect completo si necesita comprobar sesión.
        pkceMethod: 'S256',
      },
      features: [
        withAutoRefreshToken({
          onInactivityTimeout: 'logout',
          sessionTimeout: 5 * 60 * 1000,
        }),
      ],
      providers: [AutoRefreshTokenService, UserActivityService],
    }),
  ],
};
