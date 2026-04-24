import { fromData } from '../models/DashboardSummary.js';
import { fromData as _fromData } from '../models/ConsumptionChart.js';
import { defaultTimezone } from '../config/index.js';
import { getDateInTimezone, formatDate, formatISO } from '../utils/dateUtils.js';

// Inicializar servicios
import ConsumptionService from '../services/consumptionService.js';
import PredictionService from '../services/predictionService.js';
import InsightsService from '../services/insightsService.js';

const consumptionService = new ConsumptionService();
const predictionService = new PredictionService();

const insightsService = new InsightsService(consumptionService, predictionService);

class DashboardController {
  /**
   * GET /api/v1/dashboard/summary
   * Obtiene KPIs del día y próxima franja horaria de alta tarifa
   */
  static async getSummary(req, res) {
    try {
      const { date, householdId } = req.query;
      const timezone = req.query.timezone || defaultTimezone;
      
      // Validar parámetros requeridos
      if (!householdId) {
        return res.status(400).json({
          error: 'Bad Request',
          message: 'householdId is required',
          code: 'MISSING_HOUSEHOLD_ID'
        });
      }

      // Obtener datos del servicio
      const summaryData = await insightsService.getDashboardSummary(
        householdId,
        date,
        timezone
      );
      
      // Crear y validar modelo
      const summary = fromData(summaryData);
      summary.validate();
      
      // Responder con el modelo
      res.status(200).json(summary.toJSON());
      
    } catch (error) {
      DashboardController.handleError(error, res);
    }
  };

  /**
   * GET /api/v1/dashboard/consumption-chart
   * Obtiene series horarias y franjas para el gráfico
   */
  static async getConsumptionChart(req, res) {
    try {
      const { date, householdId } = req.query;
      const timezone = req.query.timezone || defaultTimezone;
      
      // Validar parámetros requeridos
      if (!householdId) {
        return res.status(400).json({
          error: 'Bad Request',
          message: 'householdId is required',
          code: 'MISSING_HOUSEHOLD_ID'
        });
      }

      // Obtener datos del servicio
      const chartData = await insightsService.getConsumptionChart(
        householdId,
        date,
        timezone
      );
      
      // Crear y validar modelo
      const chart = _fromData(chartData);
      chart.validate();
      
      // Responder con el modelo
      res.status(200).json(chart.toJSON());
      
    } catch (error) {
      DashboardController.handleError(error, res);
    }
  }

  /**
   * GET /api/v1/dashboard/recommendations
   * Lista corta de recomendaciones (mock estable hasta integrar motor IA).
   */
  static async getRecommendations(req, res) {
    try {
      const { date, householdId, limit } = req.query;
      const timezone = req.query.timezone || defaultTimezone;
      if (!householdId) {
        return res.status(400).json({
          error: 'Bad Request',
          message: 'householdId is required',
          code: 'MISSING_HOUSEHOLD_ID',
        });
      }
      const targetDate = getDateInTimezone(date, timezone);
      const lim = Math.min(10, Math.max(1, parseInt(String(limit ?? '3'), 10) || 3));
      const dateStr = formatDate(targetDate, timezone);
      const evening = formatISO(targetDate.clone().hour(22).minute(30).second(0), timezone);
      const items = [
        {
          id: 'reco-lavado-valle',
          title: 'Programa la lavadora en franja Valle',
          body: 'Traslada el ciclo a partir de las 22:00 para aprovechar la tarifa más baja.',
          suggestedStart: evening,
          estimatedSavingsCop: 1200,
          priority: 1,
        },
        {
          id: 'reco-termo-media',
          title: 'Calienta agua fuera de Punta',
          body: 'Evita el calentamiento eléctrico entre 10:00 y 13:00 y 18:00–21:00.',
          estimatedSavingsCop: 800,
          priority: 2,
        },
        {
          id: 'reco-ac-setpoint',
          title: 'Sube 1 °C el setpoint del aire',
          body: 'En horas Punta, cada grado reduce notablemente el consumo.',
          estimatedSavingsCop: 600,
          priority: 3,
        },
      ].slice(0, lim);
      res.status(200).json({ date: dateStr, items });
    } catch (error) {
      DashboardController.handleError(error, res);
    }
  }

  /**
   * GET /api/v1/dashboard/appliances/top
   * Top electrodomésticos (mock estable; el consumo real viene del servicio de consumo).
   */
  static async getAppliancesTop(req, res) {
    try {
      const { date, householdId, limit } = req.query;
      const timezone = req.query.timezone || defaultTimezone;
      if (!householdId) {
        return res.status(400).json({
          error: 'Bad Request',
          message: 'householdId is required',
          code: 'MISSING_HOUSEHOLD_ID',
        });
      }
      const targetDate = getDateInTimezone(date, timezone);
      const lim = Math.min(10, Math.max(1, parseInt(String(limit ?? '5'), 10) || 5));
      const dateStr = formatDate(targetDate, timezone);
      const items = [
        { id: 'appliance-heater-01', name: 'Calentador', category: 'WATER_HEATER', sharePercent: 92, consumptionKwh: 4.2 },
        { id: 'appliance-washer-01', name: 'Lavadora', category: 'WASHER', sharePercent: 76, consumptionKwh: 3.5 },
        { id: 'appliance-ac-01', name: 'Aire acondicionado', category: 'HVAC', sharePercent: 64, consumptionKwh: 2.9 },
        { id: 'appliance-fridge-01', name: 'Nevera', category: 'FRIDGE', sharePercent: 48, consumptionKwh: 1.8 },
        { id: 'appliance-lights-01', name: 'Iluminación', category: 'LIGHT', sharePercent: 32, consumptionKwh: 1.1 },
      ].slice(0, lim);
      res.status(200).json({ date: dateStr, metric: 'SHARE_OF_DAY', items });
    } catch (error) {
      DashboardController.handleError(error, res);
    }
  }

  static async postRecommendationApply(req, res) {
    res.status(200).json({ ok: true, id: req.params.id, action: 'apply' });
  }

  static async postRecommendationDismiss(req, res) {
    res.status(200).json({ ok: true, id: req.params.id, action: 'dismiss' });
  }

  /**
   * Manejo centralizado de errores
   */
  static handleError(error, res) {
    console.error('DashboardController Error:', error);
    
    // Errores de validación de modelo
    if (error.message.includes('Missing required field') || 
        error.message.includes('must have')) {
      return res.status(500).json({
        error: 'Internal Server Error',
        message: 'Data validation failed',
        details: error.message,
        code: 'VALIDATION_ERROR'
      });
    }
    
    // Errores de servicios externos
    if (error.message.includes('unavailable')) {
      return res.status(503).json({
        error: 'Service Unavailable',
        message: 'One or more dependent services are unavailable',
        code: 'DEPENDENCY_ERROR'
      });
    }
    
    // Error genérico
    res.status(500).json({
      error: 'Internal Server Error',
      message: error.message,
      code: 'INTERNAL_ERROR'
    });
  }
}

export default DashboardController;

// Export nombrado (funciones individuales)
export const {
  getSummary,
  getConsumptionChart,
  getRecommendations,
  getAppliancesTop,
  postRecommendationApply,
  postRecommendationDismiss,
} = DashboardController;