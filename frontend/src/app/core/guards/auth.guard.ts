import { inject } from '@angular/core';
import { Router, type CanActivateFn, type UrlTree } from '@angular/router';
import Keycloak from 'keycloak-js';
import { clearStoredKeycloakTokens } from '../auth/keycloak-direct-grant.util';

/**
 * Guard de rutas autenticadas.
 *
 * 1) Si Keycloak ya tiene sesión activa (rehidratada desde sessionStorage o por
 *    flujo SSO normal), permite el acceso.
 * 2) Si no, intenta refrescar el token (cubre el caso F5 con access expirado
 *    pero refresh aún válido). Si funciona, deja pasar.
 * 3) Si tampoco funciona, manda al login interno del SPA (no a la página de
 *    Keycloak), preservando la URL pretendida para volver tras autenticar.
 */
export const authGuard: CanActivateFn = async (_, state): Promise<boolean | UrlTree> => {
  const keycloak = inject(Keycloak);
  const router = inject(Router);

  if (keycloak.authenticated) {
    try {
      // Asegura que el access token tenga al menos 30 s de validez restante.
      await keycloak.updateToken(30);
      return true;
    } catch {
      // Refresh falló: token caducado, lo limpiamos y caemos al login interno.
    }
  }

  clearStoredKeycloakTokens();
  return router.createUrlTree(['/auth/login'], {
    queryParams: state.url && state.url !== '/auth/login' ? { returnUrl: state.url } : undefined,
  });
};
