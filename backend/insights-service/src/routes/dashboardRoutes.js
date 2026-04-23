import { Router } from 'express';
const router = Router();
import { getSummary, getConsumptionChart } from '../controllers/dashboardController.js';

/**
 * @swagger
 * /dashboard/summary:
 *   get:
 *     summary: Resumen del día (KPIs)
 *     description: Entrega los indicadores de la franja superior del dashboard
 *     tags: [Dashboard]
 *     parameters:
 *       - in: query
 *         name: householdId
 *         required: true
 *         schema:
 *           type: string
 *         description: ID de la vivienda
 *       - in: query
 *         name: date
 *         schema:
 *           type: string
 *           format: date
 *         description: Día a consultar (YYYY-MM-DD)
 *       - in: query
 *         name: timezone
 *         schema:
 *           type: string
 *           default: America/Bogota
 *         description: Zona horaria
 *     responses:
 *       200:
 *         description: KPIs del dashboard
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/DashboardSummaryResponse'
 *       400:
 *         description: Parámetros inválidos
 *       503:
 *         description: Servicio no disponible
 */
router.get('/dashboard/summary', getSummary);

/**
 * @swagger
 * /dashboard/consumption-chart:
 *   get:
 *     summary: Gráfico consumo vs predicción
 *     description: Series horarias del día y franjas para el gráfico
 *     tags: [Dashboard]
 *     parameters:
 *       - in: query
 *         name: householdId
 *         required: true
 *         schema:
 *           type: string
 *         description: ID de la vivienda
 *       - in: query
 *         name: date
 *         schema:
 *           type: string
 *           format: date
 *         description: Día a consultar (YYYY-MM-DD)
 *       - in: query
 *         name: timezone
 *         schema:
 *           type: string
 *           default: America/Bogota
 *         description: Zona horaria
 *     responses:
 *       200:
 *         description: Series horarias y franjas
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/ConsumptionChartResponse'
 *       400:
 *         description: Parámetros inválidos
 *       503:
 *         description: Servicio no disponible
 */
router.get('/dashboard/consumption-chart', getConsumptionChart);

export default router;