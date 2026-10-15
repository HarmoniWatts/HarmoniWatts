import type Keycloak from 'keycloak-js';
import { jwtDecode } from 'jwt-decode';

type KcJwt = {
  exp?: number;
  iat?: number;
  sub?: string;
  sid?: string;
  realm_access?: unknown;
  resource_access?: unknown;
};

/**
 * Tokens persistidos para sobrevivir a recargas de la pestaña (F5).
 *
 * Por qué sessionStorage y no localStorage:
 * - El flujo Resource Owner Password no genera cookie SSO en Keycloak; al
 *   recargar, `check-sso` no encuentra sesión y el guard redirige al login.
 * - Persistir por pestaña (sessionStorage) es el mejor compromiso entre
 *   continuidad de sesión y seguridad: se borra al cerrar la pestaña y no
 *   se comparte entre pestañas.
 *
 * Riesgo conocido: cualquier script ejecutado en la app puede leer estos
 * tokens (riesgo XSS). Asegúrate de no inyectar HTML sin sanitizar.
 */
const STORAGE_KEY = 'harmoniwatts.kc.tokens';

export interface StoredKcTokens {
  access_token: string;
  refresh_token: string;
  id_token?: string;
}

export function persistKeycloakTokens(tokens: StoredKcTokens): void {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(tokens));
  } catch {
    /* almacenamiento no disponible: la sesión no sobrevivirá a F5 */
  }
}

export function readStoredKeycloakTokens(): StoredKcTokens | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<StoredKcTokens>;
    if (parsed && typeof parsed.access_token === 'string' && typeof parsed.refresh_token === 'string') {
      return {
        access_token: parsed.access_token,
        refresh_token: parsed.refresh_token,
        id_token: typeof parsed.id_token === 'string' ? parsed.id_token : undefined,
      };
    }
    return null;
  } catch {
    return null;
  }
}

export function clearStoredKeycloakTokens(): void {
  try {
    sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    /* nada que hacer */
  }
}

/**
 * Aplica tokens del flujo resource owner (password) al adaptador keycloak-js.
 * Debe replicar lo que hace el `setToken` interno; si no, `updateToken()` y el
 * interceptor Bearer fallan hasta recargar la página.
 */
export function applyKeycloakResourceOwnerPasswordTokens(
  keycloak: Keycloak,
  accessToken: string,
  refreshToken: string,
  idToken?: string | null,
): void {
  const kc = keycloak as unknown as {
    token?: string;
    refreshToken?: string;
    idToken?: string;
    tokenParsed?: KcJwt;
    refreshTokenParsed?: unknown;
    idTokenParsed?: unknown;
    authenticated: boolean;
    subject?: string;
    sessionId?: string;
    realmAccess?: unknown;
    resourceAccess?: unknown;
    timeSkew?: number | null;
    tokenTimeoutHandle?: ReturnType<typeof setTimeout> | null;
    onTokenExpired?: () => void;
  };

  if (kc.tokenTimeoutHandle != null) {
    clearTimeout(kc.tokenTimeoutHandle);
    kc.tokenTimeoutHandle = null;
  }

  const timeLocal = Date.now();

  kc.refreshToken = refreshToken;
  try {
    kc.refreshTokenParsed = jwtDecode(refreshToken);
  } catch {
    delete kc.refreshTokenParsed;
  }

  if (idToken) {
    kc.idToken = idToken;
    kc.idTokenParsed = jwtDecode(idToken);
  } else {
    delete kc.idToken;
    delete kc.idTokenParsed;
  }

  kc.token = accessToken;
  const tokenParsed = jwtDecode<KcJwt>(accessToken);
  kc.tokenParsed = tokenParsed;
  kc.authenticated = true;
  kc.subject = tokenParsed.sub;
  kc.sessionId = tokenParsed.sid;
  kc.realmAccess = tokenParsed.realm_access;
  kc.resourceAccess = tokenParsed.resource_access;

  const iatSec = typeof tokenParsed.iat === 'number' ? tokenParsed.iat : Math.floor(timeLocal / 1000);
  kc.timeSkew = Math.floor(timeLocal / 1000) - iatSec;

  if (kc.onTokenExpired) {
    const exp = typeof tokenParsed.exp === 'number' ? tokenParsed.exp : 0;
    const skew = kc.timeSkew ?? 0;
    const expiresIn = (exp - Math.ceil(Date.now() / 1000) + skew) * 1000;
    if (expiresIn <= 0) {
      kc.onTokenExpired();
    } else {
      kc.tokenTimeoutHandle = setTimeout(kc.onTokenExpired, expiresIn);
    }
  }

  /* Persistimos para que F5 no obligue al usuario a iniciar sesión otra vez. */
  persistKeycloakTokens({
    access_token: accessToken,
    refresh_token: refreshToken,
    id_token: idToken ?? undefined,
  });
}
