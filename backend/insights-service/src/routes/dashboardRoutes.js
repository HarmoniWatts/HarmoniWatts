import { Router } from 'express';
const router = Router();
import {
  getSummary,
  getConsumptionChart,
  getRecommendations,
  getAppliancesTop,
  getPrediction,
  getAlerts,
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

/**
 * @swagger
 * /dashboard/alerts:
 *   get:
 *     summary: Alertas visuales (HAR-21)
 *     description: >
 *       Franja de alto precio (en punta, o empieza en ≤ 60 / ≤ 180 min) según la tarifa real de la
 *       vivienda, y consumo sobre lo habitual (última hora y acumulado del día vs. promedio de las
 *       4 semanas anteriores; +30 % LOW, +60 % MEDIUM, +100 % HIGH).
 *     tags: [Dashboard]
 *     parameters:
 *       - { in: query, name: noContrato, schema: { type: string } }
 *       - { in: query, name: codComercializadora, schema: { type: string } }
 *       - { in: query, name: idZona, schema: { type: integer } }
 *       - { in: query, name: codMercado, schema: { type: string } }
 *       - { in: query, name: estrato, schema: { type: integer } }
 *       - in: query
 *         name: at
 *         schema: { type: string, example: '2026-11-22T17:30' }
 *         description: Hora simulada (pruebas / QA). Por defecto, la hora actual.
 *     responses:
 *       200:
 *         description: Alertas ordenadas por severidad
 *       400:
 *         description: Falta el contrato y la ubicación
 */
router.get('/dashboard/alerts', getAlerts);

router.get('/dashboard/recommendations', getRecommendations);

router.get('/dashboard/appliances/top', getAppliancesTop);

router.post('/recommendations/:id/apply', postRecommendationApply);

router.post('/recommendations/:id/dismiss', postRecommendationDismiss);

export default router;