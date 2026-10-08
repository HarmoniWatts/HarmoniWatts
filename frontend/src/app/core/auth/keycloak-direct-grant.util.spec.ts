import {
  clearStoredKeycloakTokens,
  persistKeycloakTokens,
  readStoredKeycloakTokens,
} from './keycloak-direct-grant.util';

describe('tokens Keycloak en sessionStorage', () => {
  beforeEach(() => sessionStorage.clear());

  it('persiste y relee los tokens', () => {
    persistKeycloakTokens({ access_token: 'a', refresh_token: 'r', id_token: 'i' });
    expect(readStoredKeycloakTokens()).toEqual({ access_token: 'a', refresh_token: 'r', id_token: 'i' });
  });

  it('devuelve null si no hay tokens o están corruptos', () => {
    expect(readStoredKeycloakTokens()).toBeNull();
    sessionStorage.setItem('harmoniwatts.kc.tokens', '{no-json');
    expect(readStoredKeycloakTokens()).toBeNull();
  });

  it('devuelve null si falta el refresh_token', () => {
    sessionStorage.setItem('harmoniwatts.kc.tokens', JSON.stringify({ access_token: 'a' }));
    expect(readStoredKeycloakTokens()).toBeNull();
  });

  it('clearStoredKeycloakTokens borra la sesión', () => {
    persistKeycloakTokens({ access_token: 'a', refresh_token: 'r' });
    clearStoredKeycloakTokens();
    expect(readStoredKeycloakTokens()).toBeNull();
  });
});
