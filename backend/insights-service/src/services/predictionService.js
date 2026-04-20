import get from 'axios';
import { predictionServiceUrl } from '../config/index.js';

class PredictionService {
  constructor() {
    this.baseUrl = predictionServiceUrl;
  }

  async getDailyTotal(householdId, date) {
    try {
      const response = await get(
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
      const response = await get(
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

export default PredictionService;