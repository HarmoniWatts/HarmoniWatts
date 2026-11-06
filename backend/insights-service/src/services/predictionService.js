import axios from 'axios';
import config from '../config/index.js';

class PredictionService {
  constructor() {
    this.baseUrl = config.predictionServiceUrl;
    this.client = axios.create({
      baseURL: this.baseUrl,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      }
    });
  }

  async getDailyTotal(contrato, date) {
    try {
      const params = date ? { date } : {};
      const response = await this.client.get(`/prediction/daily-total/${encodeURIComponent(contrato.noContrato)}`, { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching prediction total:', error.message);
      return null;
    }
  }

  // Método para obtener series horarias (para el gráfico)
  async getHourlySeries(contrato, date) {
    try {
      const params = date ? { date } : {};
      const response = await this.client.get(`/prediction/daily-series/${encodeURIComponent(contrato.noContrato)}`, { params });
      
      // Transformar al formato esperado
      return {
        series: response.data.series || response.data.predictedKwh || [],
        metadata: response.data.metadata || {}
      };
    } catch (error) {
      console.error('Error fetching prediction hourly series:', error.message);
      return null;
    }
  }

  // Método para compatibilidad (si existe código que use getDailySeries)
  async getDailySeries(contrato, date) {
    return this.getHourlySeries(contrato, date);
  }
}

export default PredictionService;