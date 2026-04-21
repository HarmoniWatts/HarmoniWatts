import { fromData } from '../models/DashboardSummary.js';
import { fromData as _fromData } from '../models/ConsumptionChart.js';
import { defaultTimezone } from '../config/index.js';

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
  };

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
  getConsumptionChart
} = DashboardController;