import { Router } from 'express';
const router = Router();
import { getSummary, getConsumptionChart } from '../controllers/dashboardController.js';

/**
 * Dashboard Routes
 * Base path: /api/v1/dashboard
 */

// GET /api/v1/dashboard/summary - Obtener KPIs del día y próxima franja cara
router.get('/dashboard/summary', getSummary);

// GET /api/v1/dashboard/consumption-chart - Obtener series horarias para gráfico
router.get('/dashboard/consumption-chart', getConsumptionChart);

export default router;