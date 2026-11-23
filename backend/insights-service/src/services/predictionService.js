import axios from 'axios';
import config from '../config/index.js';

/** Caché corta: el gráfico del día y la tarjeta de predicción piden el mismo pronóstico. */
const CACHE_TTL_MS = 10 * 60 * 1000;

/**
 * Cliente de prediction-service (HAR-108 / HAR-25): modelo MLflow que pronostica el consumo
 * horario de un contrato y evalúa su precisión contra el consumo real de los últimos días.
 */
class PredictionService {
  constructor() {
    this.baseUrl = config.predictionServiceUrl;
    this.client = axios.create({
      baseURL: this.baseUrl,
      // La primera llamada carga ~3 semanas de historia y ejecuta el modelo dos veces
      timeout: 60000,
      headers: { 'Content-Type': 'application/json' },
    });
    this.cache = new Map();
  }

  /**
   * Pronóstico del contrato: { historico, futuro, confianza, ... } (formato de prediction-service).
   * Lanza el error de axios; con 404 el contrato no tiene historia suficiente.
   */
  async getPronostico(contrato, { diasPasados = 7, diasFuturos = 7 } = {}) {
    const key = `${contrato.noContrato}|${contrato.codComercializadora}|${diasPasados}|${diasFuturos}`;
    const hit = this.cache.get(key);
    if (hit && Date.now() - hit.at < CACHE_TTL_MS) {
      return hit.data;
    }
    const url =
      `/api/v1/prediction/contrato/${encodeURIComponent(contrato.noContrato)}` +
      `/${encodeURIComponent(contrato.codComercializadora)}/pronostico`;
    const response = await this.client.get(url, {
      params: { dias_pasados: diasPasados, dias_futuros: diasFuturos },
    });
    this.cache.set(key, { at: Date.now(), data: response.data });
    return response.data;
  }

  /** Igual que getPronostico pero devuelve null si falla (para no romper el gráfico del día). */
  async getPronosticoSeguro(contrato, opts) {
    try {
      return await this.getPronostico(contrato, opts);
    } catch (error) {
      const status = error.response?.status;
      console.error(`Pronóstico no disponible (${status ?? error.code ?? 'error'}): ${error.message}`);
      return null;
    }
  }

  /**
   * Total diario pronosticado (lo usa el resumen). prediction-service no expone un total diario:
   * se devuelve null y el resumen sigue funcionando sin él.
   */
  async getDailyTotal() {
    return null;
  }
}

export default PredictionService;
