/**
 * Cliente de Keycloak Admin API para crear usuarios.
 */
import { config } from './config.js';

const { url: baseUrl, realm, adminUsername, adminPassword, frontendClientId } = config.keycloak;

export async function getAdminToken() {
  const res = await fetch(`${baseUrl}/realms/master/protocol/openid-connect/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'password',
      client_id: 'admin-cli',
      username: adminUsername,
      password: adminPassword,
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Keycloak admin token failed: ${res.status} ${text}`);
  }

  const data = await res.json();
  return data.access_token;
}

/**
 * Crea un usuario en Keycloak y le asigna la contraseña.
 * @param {string} accessToken - Token de admin
 * @param {Object} payload - { firstName, lastName, email, username, password, city? }
 * @returns {{ userId: string }}
 */
export async function createUser(accessToken, payload) {
  const { firstName, lastName, email, username, password, city } = payload;
  const userBody = {
    username: username || email,
    email: email || username,
    firstName: firstName || '',
    lastName: lastName || '',
    enabled: true,
    emailVerified: false,
  };
  if (city) userBody.attributes = { city: [city] };

  const createRes = await fetch(`${baseUrl}/admin/realms/${realm}/users`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(userBody),
  });

  if (createRes.status === 409) {
    throw new Error('El correo o usuario ya está registrado.');
  }
  if (!createRes.ok) {
    const errText = await createRes.text();
    throw new Error(errText || `Keycloak create user failed: ${createRes.status}`);
  }

  const location = createRes.headers.get('Location');
  const userId = location ? location.split('/').pop() : null;
  if (!userId) throw new Error('No se obtuvo el ID del usuario creado.');

  const credRes = await fetch(`${baseUrl}/admin/realms/${realm}/users/${userId}/reset-password`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ type: 'password', value: password, temporary: false }),
  });

  if (!credRes.ok) {
    const errText = await credRes.text();
    throw new Error(errText || 'Error al asignar contraseña.');
  }

  await sendVerifyEmail(accessToken, userId);

  return { userId };
}

/**
 * Envía el correo de verificación al usuario (Keycloak debe tener SMTP configurado).
 * PUT /admin/realms/{realm}/users/{userId}/send-verify-email
 */
async function sendVerifyEmail(accessToken, userId) {
  const res = await fetch(`${baseUrl}/admin/realms/${realm}/users/${userId}/send-verify-email`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
  });
  if (!res.ok) {
    const errText = await res.text();
    console.warn('[harmoni-register] No se pudo enviar correo de verificación:', res.status, errText);
  }
}

/**
 * Busca un usuario en Keycloak por email (coincidencia exacta).
 * @param {string} accessToken - Token de admin
 * @param {string} email - Email del usuario
 * @returns {Promise<{ id: string } | null>}
 */
export async function findUserByEmail(accessToken, email) {
  const q = new URLSearchParams({ email: email.trim() });
  const res = await fetch(`${baseUrl}/admin/realms/${realm}/users?${q}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!res.ok) return null;
  const users = await res.json();
  const user = Array.isArray(users) && users.length > 0 ? users[0] : null;
  return user ? { id: user.id } : null;
}

/**
 * Envía el correo de restablecimiento de contraseña al usuario (Keycloak debe tener SMTP configurado).
 * PUT /admin/realms/{realm}/users/{userId}/execute-actions-email
 */
export async function sendResetPasswordEmail(accessToken, userId) {
  const res = await fetch(`${baseUrl}/admin/realms/${realm}/users/${userId}/execute-actions-email`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(['UPDATE_PASSWORD']),
  });
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(errText || `execute-actions-email failed: ${res.status}`);
  }
}

/**
 * Verifica contraseña actual (resource owner password) con el cliente público del SPA.
 */
export async function verifyResourceOwnerPassword(username, password) {
  const body = new URLSearchParams({
    grant_type: 'password',
    client_id: frontendClientId,
    username,
    password,
  });
  const res = await fetch(`${baseUrl}/realms/${realm}/protocol/openid-connect/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  });
  if (res.status === 401) {
    const err = new Error('PASSWORD_INVALID');
    err.code = 'PASSWORD_INVALID';
    throw err;
  }
  if (!res.ok) {
    const t = await res.text();
    throw new Error(`verify_password_failed: ${res.status} ${t}`);
  }
}

export async function getUserRepresentation(accessToken, userId) {
  const res = await fetch(`${baseUrl}/admin/realms/${realm}/users/${userId}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (res.status === 404) {
    throw new Error('Usuario no encontrado en Keycloak.');
  }
  if (!res.ok) {
    const t = await res.text();
    throw new Error(`get_user_failed: ${res.status} ${t}`);
  }
  return res.json();
}

export async function putUserRepresentation(accessToken, userId, userJson) {
  const res = await fetch(`${baseUrl}/admin/realms/${realm}/users/${userId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(userJson),
  });
  if (!res.ok) {
    const t = await res.text();
    throw new Error(`put_user_failed: ${res.status} ${t}`);
  }
}

/**
 * Actualiza nombre, apellidos y opcionalmente email (Admin API).
 */
export async function updateProfileByAdmin(accessToken, userId, { firstName, lastName, email }) {
  const user = await getUserRepresentation(accessToken, userId);
  user.firstName = String(firstName).trim();
  user.lastName = String(lastName).trim();
  if (email != null && String(email).trim() !== '') {
    const em = String(email).trim();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(em)) {
      throw new Error('Email no válido.');
    }
    user.email = em;
  }
  await putUserRepresentation(accessToken, userId, user);
}

export async function adminResetUserPassword(accessToken, userId, newPassword) {
  const res = await fetch(`${baseUrl}/admin/realms/${realm}/users/${userId}/reset-password`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ type: 'password', value: newPassword, temporary: false }),
  });
  if (!res.ok) {
    const t = await res.text();
    throw new Error(`reset_password_failed: ${res.status} ${t}`);
  }
}
