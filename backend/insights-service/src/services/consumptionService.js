import get from 'axios';
import { consumptionServiceUrl } from '../config/index.js';

class ConsumptionService {
  constructor() {
    this.baseUrl = consumptionServiceUrl;
  }

  async getCurrentConsumption(householdId) {
    try {
      const response = await get(
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
      const response = await get(
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
      const response = await get(
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

export default ConsumptionService;