/**
 * Verificación de JWT de acceso de Keycloak (JWKS del realm).
 */
import { createRemoteJWKSet, jwtVerify } from 'jose';
import { config } from './config.js';

const { url: baseUrl, realm } = config.keycloak;

const jwksUrl = `${baseUrl}/realms/${realm}/protocol/openid-connect/certs`;
const JWKS = createRemoteJWKSet(new URL(jwksUrl));

/**
 * Middleware: exige Authorization: Bearer y valida firma/exp contra el realm configurado.
 */
export async function authenticateBearer(req, res, next) {
  try {
    const auth = req.headers.authorization;
    if (!auth?.startsWith('Bearer ')) {
      return res.status(401).json({ message: 'Se requiere autenticación.' });
    }
    const token = auth.slice(7);
    const { payload } = await jwtVerify(token, JWKS, {
      algorithms: ['RS256', 'RS384', 'RS512'],
      clockTolerance: '30s',
    });
    const realmSuffix = `/realms/${realm}`;
    if (payload.iss && typeof payload.iss === 'string' && !payload.iss.includes(realmSuffix)) {
      return res.status(401).json({ message: 'Token no emitido para este realm.' });
    }
    if (!payload.sub) {
      return res.status(401).json({ message: 'Token sin sujeto (sub).' });
    }
    req.keycloakJwt = payload;
    next();
  } catch (e) {
    console.warn('[harmoni-register] JWT inválido:', e?.message || e);
    return res.status(401).json({ message: 'Token inválido o expirado.' });
  }
}
