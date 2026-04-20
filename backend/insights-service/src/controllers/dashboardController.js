const config = require('../config');

class DashboardController {
  constructor(insightsService) {
    this.insightsService = insightsService;
  }

  getSummary = async (req, res) => {
    try {
      const { date, householdId } = req.query;
      const timezone = req.query.timezone || config.defaultTimezone;
      
      // Validate householdId
      if (!householdId) {
        return res.status(400).json({
          error: 'Bad Request',
          message: 'householdId is required'
        });
      }

      const summary = await this.insightsService.getDashboardSummary(
        householdId,
        date,
        timezone
      );
      
      res.status(200).json(summary);
    } catch (error) {
      console.error('Error in getSummary:', error);
      
      if (error.message.includes('unavailable')) {
        return res.status(503).json({
          error: 'Service Unavailable',
          message: 'One or more dependent services are unavailable'
        });
      }
      
      res.status(500).json({
        error: 'Internal Server Error',
        message: error.message
      });
    }
  };

  getConsumptionChart = async (req, res) => {
    try {
      const { date, householdId } = req.query;
      const timezone = req.query.timezone || config.defaultTimezone;
      
      // Validate householdId
      if (!householdId) {
        return res.status(400).json({
          error: 'Bad Request',
          message: 'householdId is required'
        });
      }

      const chartData = await this.insightsService.getConsumptionChart(
        householdId,
        date,
        timezone
      );
      
      res.status(200).json(chartData);
    } catch (error) {
      console.error('Error in getConsumptionChart:', error);
      
      if (error.message.includes('unavailable')) {
        return res.status(503).json({
          error: 'Service Unavailable',
          message: 'One or more dependent services are unavailable'
        });
      }
      
      res.status(500).json({
        error: 'Internal Server Error',
        message: error.message
      });
    }
  };
}

module.exports = DashboardController;