/**
 * Rutas del microservicio de registro.
 */
import { getAdminToken, createUser, findUserByEmail, sendResetPasswordEmail } from './keycloak.js';

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
