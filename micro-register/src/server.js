/**
 * Punto de entrada del microservicio de registro de usuarios.
 * Expone POST /api/auth/register y GET /health.
 */
import app from './app.js';
import { config } from './config.js';

const { port, keycloak } = config;

app.listen(port, () => {
  console.log(`Micro-register escuchando en http://localhost:${port}`);
  console.log(`  POST /api/auth/register  - Registro de usuarios (Keycloak)`);
  console.log(`  GET  /health            - Estado del servicio`);
  console.log(`Keycloak: ${keycloak.url}, realm: ${keycloak.realm}`);
});
