/**
 * Configuración del microservicio (variables de entorno).
 */
const env = process.env;

const keycloakUrl = (env.KEYCLOAK_URL || 'http://localhost:8080').replace(/\/$/, '');
const realm = env.KEYCLOAK_REALM || 'harmoniwatts';
const adminUsername = env.KEYCLOAK_ADMIN_USERNAME || env.KEYCLOAK_ADMIN || 'admin';
const adminPassword = env.KEYCLOAK_ADMIN_PASSWORD || '';

if (!adminPassword && process.env.NODE_ENV !== 'test') {
  console.warn('KEYCLOAK_ADMIN_PASSWORD no está definida; el registro fallará hasta configurarla.');
}

export const config = {
  port: Number(env.PORT) || 8081,
  keycloak: {
    url: keycloakUrl,
    realm,
    adminUsername,
    adminPassword,
  },
};
