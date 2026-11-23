import { Router } from 'express';
const router = Router();
import {
  getSummary,
  getConsumptionChart,
  getRecommendations,
  getAppliancesTop,
  getPrediction,
  postRecommendationApply,
  postRecommendationDismiss,
} from '../controllers/dashboardController.js';

/**
 * @swagger
 * /dashboard/summary:
 *   get:
 *     summary: Resumen del día (KPIs)
 *     description: Entrega los indicadores de la franja superior del dashboard
 *     tags: [Dashboard]
 *     parameters:
 *       - in: query
 *         name: noContrato
 *         required: true
 *         schema:
 *           type: string
 *         description: Número de contrato de la vivienda con la comercializadora
 *       - in: query
 *         name: codComercializadora
 *         required: true
 *         schema:
 *           type: string
 *         description: Código de la comercializadora (ej. ENERTOTAL)
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
 *         name: noContrato
 *         required: true
 *         schema:
 *           type: string
 *         description: Número de contrato de la vivienda con la comercializadora
 *       - in: query
 *         name: codComercializadora
 *         required: true
 *         schema:
 *           type: string
 *         description: Código de la comercializadora (ej. ENERTOTAL)
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

/**
 * @swagger
 * /dashboard/prediction:
 *   get:
 *     summary: Predicción de consumo vs real y próximos días (HAR-25)
 *     description: >
 *       Predicción del modelo (prediction-service) comparada con el consumo real de los últimos
 *       días, pronóstico horario de los próximos días con rango y nivel de confianza.
 *       Sin historia suficiente responde available=false.
 *     tags: [Dashboard]
 *     parameters:
 *       - in: query
 *         name: noContrato
 *         required: true
 *         schema: { type: string }
 *       - in: query
 *         name: codComercializadora
 *         required: true
 *         schema: { type: string }
 *       - in: query
 *         name: diasPasados
 *         schema: { type: integer, minimum: 0, maximum: 7, default: 7 }
 *       - in: query
 *         name: diasFuturos
 *         schema: { type: integer, minimum: 1, maximum: 7, default: 7 }
 *     responses:
 *       200:
 *         description: Pronóstico y confianza (o available=false si falta historia)
 *       400:
 *         description: Falta el contrato
 *       503:
 *         description: prediction-service no disponible
 */
router.get('/dashboard/prediction', getPrediction);

router.get('/dashboard/recommendations', getRecommendations);

router.get('/dashboard/appliances/top', getAppliancesTop);

router.post('/recommendations/:id/apply', postRecommendationApply);

router.post('/recommendations/:id/dismiss', postRecommendationDismiss);

export default router;