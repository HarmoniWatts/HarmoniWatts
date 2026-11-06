import axios from 'axios';
import config from '../config/index.js';

/** Segmento de ruta del consumption-service: /{no_contrato}/{cod_comercializadora}. */
export function cuentaPath({ noContrato, codComercializadora }) {
  return `${encodeURIComponent(noContrato)}/${encodeURIComponent(codComercializadora)}`;
}

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

  // GET /api/v1/consumption/current/{no_contrato}/{cod_comercializadora}
  async getCurrentConsumption(contrato) {
    try {
      const response = await this.client.get(`/api/v1/consumption/current/${cuentaPath(contrato)}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching current consumption:', error.message);
      throw new Error('Consumption service unavailable');
    }
  }

  // GET /api/v1/consumption/daily-total/{no_contrato}/{cod_comercializadora}
  async getDailyTotal(contrato, date, timezone) {
    try {
      const params = {};
      if (date) params.date = date;
      if (timezone) params.timezone = timezone;
      const response = await this.client.get(`/api/v1/consumption/daily-total/${cuentaPath(contrato)}`, { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching daily total:', error.message);
      throw new Error('Consumption service unavailable');
    }
  }

  // GET /api/v1/consumption/series/hourly/{no_contrato}/{cod_comercializadora}
  async getHourlySeries(contrato, date, timezone) {
    try {
      const params = {};
      if (date) params.date = date;
      if (timezone) params.timezone = timezone;
      const response = await this.client.get(`/api/v1/consumption/series/hourly/${cuentaPath(contrato)}`, { params });
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

  // GET /api/v1/consumption/series/daily/{no_contrato}/{cod_comercializadora}
  async getDailySeries(contrato, year, month, timezone) {
    try {
      const params = { year, month };
      if (timezone) params.timezone = timezone;
      const response = await this.client.get(`/api/v1/consumption/series/daily/${cuentaPath(contrato)}`, {
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

  // GET /api/v1/consumption/series/monthly/{no_contrato}/{cod_comercializadora}
  async getMonthlySeries(contrato, year, timezone) {
    try {
      const params = { year };
      if (timezone) params.timezone = timezone;
      const response = await this.client.get(`/api/v1/consumption/series/monthly/${cuentaPath(contrato)}`, {
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

  // GET /api/v1/consumption/series/yearly/{no_contrato}/{cod_comercializadora}
  async getYearlySeries(contrato, startYear, endYear, timezone) {
    try {
      const params = { start_year: startYear, end_year: endYear };
      if (timezone) params.timezone = timezone;
      const response = await this.client.get(`/api/v1/consumption/series/yearly/${cuentaPath(contrato)}`, {
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
  async getDailySeriesCompatible(contrato, date, timezone) {
    return await this.getHourlySeries(contrato, date, timezone);
  }
}

export default ConsumptionService;