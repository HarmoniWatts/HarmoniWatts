/**
 * Aplicación Express del microservicio de registro.
 */
import express from 'express';
import { handleRegister, handleHealth } from './routes.js';

const app = express();

app.use(express.json());

app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') {
    res.sendStatus(204);
    return;
  }
  next();
});

app.get('/health', handleHealth);
app.post('/api/auth/register', handleRegister);

app.use((req, res) => {
  res.status(404).json({ message: 'Not Found' });
});

export default app;
