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
}
