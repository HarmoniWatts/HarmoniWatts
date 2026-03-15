import { inject } from '@angular/core';
import { type CanActivateFn } from '@angular/router';
import Keycloak from 'keycloak-js';

export const authGuard: CanActivateFn = async (_, state) => {
  const keycloak = inject(Keycloak);
  if (keycloak.authenticated) {
    return true;
  }
  await keycloak.login({
    redirectUri: state.url ? window.location.origin + state.url : window.location.origin + '/dashboard',
  });
  return false;
};
