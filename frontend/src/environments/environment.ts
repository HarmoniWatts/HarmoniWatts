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
};
