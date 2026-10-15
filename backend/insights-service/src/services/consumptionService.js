import axios from 'axios';
import config from '../config/index.js';

class ConsumptionService {
  constructor() {
    this.baseUrl = config.consumptionServiceUrl;
    this.client = axios.create({
      baseURL: this.baseUrl,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      }
    });
  }

  // GET /api/v1/consumption/current/{household_id}
  async getCurrentConsumption(householdId) {
    try {
      const response = await this.client.get(`/api/v1/consumption/current/${householdId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching current consumption:', error.message);
      throw new Error('Consumption service unavailable');
    }
  }

  // GET /api/v1/consumption/daily-total/{household_id}
  async getDailyTotal(householdId, date, timezone) {
    try {
      const params = {};
      if (date) params.date = date;
      if (timezone) params.timezone = timezone;
      const response = await this.client.get(`/api/v1/consumption/daily-total/${householdId}`, { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching daily total:', error.message);
      throw new Error('Consumption service unavailable');
    }
  }

  // GET /api/v1/consumption/series/hourly/{household_id}
  async getHourlySeries(householdId, date, timezone) {
    try {
      const params = {};
      if (date) params.date = date;
      if (timezone) params.timezone = timezone;
      const response = await this.client.get(`/api/v1/consumption/series/hourly/${householdId}`, { params });
      // Transformar al formato esperado
      return {
        series: response.data.values_kwh || [],
        metadata: response.data.metadata || {}
      };
    } catch (error) {
      console.error('Error fetching hourly series:', error.message);
      throw new Error('Consumption service unavailable');
    }
  }

  // GET /api/v1/consumption/series/daily/{household_id}
  async getDailySeries(householdId, year, month, timezone) {
    try {
      const params = { year, month };
      if (timezone) params.timezone = timezone;
      const response = await this.client.get(`/api/v1/consumption/series/daily/${householdId}`, {
        params,
      });
      
      return {
        series: response.data.values || response.data.consumption || [],
        metadata: response.data.metadata || {}
      };
    } catch (error) {
      console.error('Error fetching daily series:', error.message);
      throw new Error('Consumption service unavailable');
    }
  }

  // GET /api/v1/consumption/series/monthly/{household_id}
  async getMonthlySeries(householdId, year, timezone) {
    try {
      const params = { year };
      if (timezone) params.timezone = timezone;
      const response = await this.client.get(`/api/v1/consumption/series/monthly/${householdId}`, {
        params,
      });
      
      return {
        series: response.data.values || response.data.consumption || [],
        metadata: response.data.metadata || {}
      };
    } catch (error) {
      console.error('Error fetching monthly series:', error.message);
      throw new Error('Consumption service unavailable');
    }
  }

  // GET /api/v1/consumption/series/yearly/{household_id}
  async getYearlySeries(householdId, startYear, endYear, timezone) {
    try {
      const params = { start_year: startYear, end_year: endYear };
      if (timezone) params.timezone = timezone;
      const response = await this.client.get(`/api/v1/consumption/series/yearly/${householdId}`, {
        params,
      });
      
      return {
        series: response.data.values || response.data.consumption || [],
        metadata: response.data.metadata || {}
      };
    } catch (error) {
      console.error('Error fetching yearly series:', error.message);
      throw new Error('Consumption service unavailable');
    }
  }

  // Método de compatibilidad para mantener la interfaz existente
  async getDailySeriesCompatible(householdId, date, timezone) {
    return await this.getHourlySeries(householdId, date, timezone);
  }
}

export default ConsumptionService;