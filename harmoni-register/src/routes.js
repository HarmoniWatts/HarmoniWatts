/**
 * Rutas del microservicio de registro y cuenta Keycloak.
 */
import {
  getAdminToken,
  createUser,
  findUserByEmail,
  sendResetPasswordEmail,
  updateProfileByAdmin,
  verifyResourceOwnerPassword,
  adminResetUserPassword,
} from './keycloak.js';

function validatePayload(body) {
  const errors = [];
  if (!body.email?.trim()) errors.push('email es obligatorio');
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(body.email.trim())) errors.push('email no válido');
  if (!body.password || body.password.length < 8) errors.push('la contraseña debe tener al menos 8 caracteres');
  if (!body.firstName?.trim()) errors.push('firstName es obligatorio');
  if (!body.lastName?.trim()) errors.push('lastName es obligatorio');
  return errors;
}

export async function handleRegister(req, res) {
  const body = req.body || {};
  const validationErrors = validatePayload(body);
  if (validationErrors.length > 0) {
    res.status(400).json({ message: validationErrors.join('; ') });
    return;
  }

  const payload = {
    firstName: body.firstName.trim(),
    lastName: body.lastName.trim(),
    email: body.email.trim(),
    username: body.username?.trim() || body.email.trim(),
    password: body.password,
    city: body.city?.trim() || undefined,
  };

  try {
    const token = await getAdminToken();
    await createUser(token, payload);
    res.status(201).json({ success: true });
  } catch (err) {
    const message = err.message || 'Error al crear la cuenta.';
    res.status(400).json({ message });
  }
}

export async function handleForgotPassword(req, res) {
  const body = req.body || {};
  const email = typeof body.email === 'string' ? body.email.trim() : '';
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    res.status(400).json({ message: 'Indica un correo electrónico válido.' });
    return;
  }
  try {
    const token = await getAdminToken();
    const user = await findUserByEmail(token, email);
    if (user) {
      await sendResetPasswordEmail(token, user.id);
    }
    // Siempre 200 para no revelar si el usuario existe (evitar enumeración de cuentas).
    res.status(200).json({ success: true });
  } catch (err) {
    console.warn('[harmoni-register] forgot-password error:', err.message);
    res.status(200).json({ success: true });
  }
}

export function handleHealth(req, res) {
  res.status(200).json({ status: 'ok', service: 'harmoni-register' });
}

/** PUT /api/auth/profile — Bearer JWT; body: { firstName, lastName, email? } */
export async function handleUpdateProfile(req, res) {
  const sub = req.keycloakJwt.sub;
  const body = req.body || {};
  const firstName = typeof body.firstName === 'string' ? body.firstName.trim() : '';
  const lastName = typeof body.lastName === 'string' ? body.lastName.trim() : '';
  const emailRaw = typeof body.email === 'string' ? body.email.trim() : '';
  if (!firstName || !lastName) {
    res.status(400).json({ message: 'Nombre y apellido son obligatorios.' });
    return;
  }
  if (emailRaw && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailRaw)) {
    res.status(400).json({ message: 'Email no válido.' });
    return;
  }
  try {
    const adminToken = await getAdminToken();
    await updateProfileByAdmin(adminToken, sub, {
      firstName,
      lastName,
      email: emailRaw || undefined,
    });
    res.status(204).end();
  } catch (err) {
    console.error('[harmoni-register] update profile:', err);
    res.status(502).json({ message: err.message || 'No se pudo actualizar el perfil.' });
  }
}

/** PUT /api/auth/password — Bearer JWT; body: { currentPassword, newPassword } */
export async function handleChangePassword(req, res) {
  const sub = req.keycloakJwt.sub;
  const payload = req.keycloakJwt;
  const body = req.body || {};
  const currentPassword = body.currentPassword;
  const newPassword = body.newPassword;
  if (!currentPassword || typeof currentPassword !== 'string') {
    res.status(400).json({ message: 'Indica la contraseña actual.' });
    return;
  }
  if (!newPassword || typeof newPassword !== 'string' || newPassword.length < 8) {
    res.status(400).json({ message: 'La nueva contraseña debe tener al menos 8 caracteres.' });
    return;
  }
  const loginHint = payload.preferred_username || payload.email;
  if (!loginHint) {
    res.status(400).json({ message: 'El token no incluye preferred_username ni email.' });
    return;
  }
  try {
    try {
      await verifyResourceOwnerPassword(String(loginHint), currentPassword);
    } catch (e) {
      if (e.code === 'PASSWORD_INVALID' || e.message === 'PASSWORD_INVALID') {
        res.status(401).json({ message: 'La contraseña actual no es correcta.' });
        return;
      }
      throw e;
    }
    const adminToken = await getAdminToken();
    await adminResetUserPassword(adminToken, sub, newPassword);
    res.status(204).end();
  } catch (err) {
    console.error('[harmoni-register] change password:', err);
    res.status(502).json({ message: err.message || 'No se pudo cambiar la contraseña.' });
  }
}
