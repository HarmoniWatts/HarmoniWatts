const axios = require('axios');
const config = require('../config');

class PredictionService {
  constructor() {
    this.baseUrl = config.predictionServiceUrl;
  }

  async getDailyTotal(householdId, date) {
    try {
      const response = await axios.get(
        `${this.baseUrl}/prediction/daily-total/${householdId}`,
        { params: { date } }
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching prediction total:', error.message);
      // Return null if prediction service is unavailable
      return null;
    }
  }

  async getDailySeries(householdId, date) {
    try {
      const response = await axios.get(
        `${this.baseUrl}/prediction/daily-series/${householdId}`,
        { params: { date } }
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching prediction series:', error.message);
      // Return null if prediction service is unavailable
      return null;
    }
  }
}

module.exports = PredictionService;