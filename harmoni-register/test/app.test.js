import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';

process.env.NODE_ENV = 'test';
const { default: app } = await import('../src/app.js');

let server;
let baseUrl;

before(async () => {
  server = app.listen(0);
  await new Promise((resolve) => server.once('listening', resolve));
  baseUrl = `http://127.0.0.1:${server.address().port}`;
});

after(() => server.close());

const postJson = (path, body) =>
  fetch(`${baseUrl}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

test('GET /health responde ok', async () => {
  const res = await fetch(`${baseUrl}/health`);
  assert.equal(res.status, 200);
  assert.deepEqual(await res.json(), { status: 'ok', service: 'harmoni-register' });
});

test('POST /api/auth/register valida campos obligatorios', async () => {
  const res = await postJson('/api/auth/register', { email: 'no-es-correo', password: '123' });
  assert.equal(res.status, 400);
  const { message } = await res.json();
  assert.match(message, /email no válido/);
  assert.match(message, /al menos 8 caracteres/);
  assert.match(message, /firstName es obligatorio/);
  assert.match(message, /lastName es obligatorio/);
});

test('POST /api/auth/forgot-password rechaza correos inválidos', async () => {
  const res = await postJson('/api/auth/forgot-password', { email: 'x' });
  assert.equal(res.status, 400);
});

test('PUT /api/auth/profile sin Bearer devuelve 401', async () => {
  const res = await fetch(`${baseUrl}/api/auth/profile`, { method: 'PUT' });
  assert.equal(res.status, 401);
});

test('OPTIONS responde 204 con cabeceras CORS', async () => {
  const res = await fetch(`${baseUrl}/api/auth/register`, { method: 'OPTIONS' });
  assert.equal(res.status, 204);
  assert.equal(res.headers.get('access-control-allow-origin'), '*');
});

test('ruta desconocida devuelve 404', async () => {
  const res = await fetch(`${baseUrl}/no-existe`);
  assert.equal(res.status, 404);
});
