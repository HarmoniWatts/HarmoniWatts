const axios = require('axios');
const config = require('../config');

class ConsumptionService {
  constructor() {
    this.baseUrl = config.consumptionServiceUrl;
  }

  async getCurrentConsumption(householdId) {
    try {
      const response = await axios.get(
        `${this.baseUrl}/consumption/current/${householdId}`
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching current consumption:', error.message);
      throw new Error('Consumption service unavailable');
    }
  }

  async getDailyTotal(householdId, date) {
    try {
      const response = await axios.get(
        `${this.baseUrl}/consumption/daily-total/${householdId}`,
        { params: { date } }
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching daily total:', error.message);
      throw new Error('Consumption service unavailable');
    }
  }

  async getDailySeries(householdId, date) {
    try {
      const response = await axios.get(
        `${this.baseUrl}/consumption/daily-series/${householdId}`,
        { params: { date } }
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching daily series:', error.message);
      throw new Error('Consumption service unavailable');
    }
  }
}

module.exports = ConsumptionService;