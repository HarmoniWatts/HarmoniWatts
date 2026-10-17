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
import { readStoredKeycloakTokens } from './core/auth/keycloak-direct-grant.util';

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

const electroBase = (environment.electrodomesticosApiBaseUrl ?? '').replace(/\/$/, '');
const electrodomesticosBearerCondition = electroBase
  ? createInterceptorCondition<IncludeBearerTokenCondition>({
      urlPattern: new RegExp(`^${escapeRegExp(electroBase)}(/.*)?$`, 'i'),
      bearerPrefix: 'Bearer',
    })
  : null;

const harmoniRegBase = (environment.harmoniRegisterBaseUrl ?? '').replace(/\/$/, '');
const harmoniRegisterBearerCondition =
  harmoniRegBase && harmoniRegBase !== apiBase
    ? createInterceptorCondition<IncludeBearerTokenCondition>({
        urlPattern: new RegExp(`^${escapeRegExp(harmoniRegBase)}(/.*)?$`, 'i'),
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
      useValue: [
        keycloakBearerCondition,
        apiBearerCondition,
        ...(viviendaBearerCondition ? [viviendaBearerCondition] : []),
        ...(electrodomesticosBearerCondition ? [electrodomesticosBearerCondition] : []),
        ...(harmoniRegisterBearerCondition ? [harmoniRegisterBearerCondition] : []),
      ],
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
        // Rehidratación de sesión tras F5: si la pestaña tiene tokens persistidos
        // del flujo Direct Grant, los pasamos a `init()`. Keycloak validará el
        // access token y, si está expirado, intentará refrescarlo con el refresh
        // token. Si el refresh ya no es válido, queda no-autenticado y el guard
        // mandará al login del SPA (sin saltar a la página de Keycloak).
        ...(() => {
          const stored = readStoredKeycloakTokens();
          if (!stored) return {};
          return {
            token: stored.access_token,
            refreshToken: stored.refresh_token,
            ...(stored.id_token ? { idToken: stored.id_token } : {}),
          };
        })(),
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
