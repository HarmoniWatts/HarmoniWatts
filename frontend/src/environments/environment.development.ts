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
};
