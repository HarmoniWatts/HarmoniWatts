import axios from 'axios';
import config from '../config/index.js';

const CACHE_TTL_MS = 30 * 60 * 1000;

/**
 * Cliente de tariff-service por ubicación de la vivienda (zona, mercado, estrato).
 * Si el mes aún no está publicado usa el último mes publicado (como el frontend).
 */
class TariffService {
  constructor() {
    this.client = axios.create({ baseURL: config.tariffServiceUrl, timeout: 15000 });
    this.cache = new Map();
  }

  /** precios[] (hora 1–24, tipo_hora, precio) de la tarifa vigente, o null si no hay. */
  async getPreciosVigentes(ubicacion, fecha) {
    const key = `${ubicacion.idZona}|${ubicacion.codMercado}|${ubicacion.estrato}|${fecha}`;
    const hit = this.cache.get(key);
    if (hit && Date.now() - hit.at < CACHE_TTL_MS) return hit.data;
    const params = { id_zona: ubicacion.idZona, cod_mercado: ubicacion.codMercado, estrato: ubicacion.estrato };
    let data = null;
    try {
      data = (await this.client.get('/api/v1/tariff/ubicacion/tarifa', { params: { ...params, fecha } })).data;
    } catch (error) {
      if (error.response?.status !== 404) throw error;
      data = await this.ultimaPublicada(params, Number(fecha.slice(0, 4)));
    }
    const precios = data?.precios ?? null;
    this.cache.set(key, { at: Date.now(), data: precios });
    return precios;
  }

  async ultimaPublicada(params, anio, intentos = 2) {
    if (intentos <= 0) return null;
    const cal = (await this.client.get('/api/v1/tariff/ubicacion/calendario', { params: { ...params, anio } })).data;
    const mes = [...(cal?.meses ?? [])].reverse().find((m) => m.publicado);
    if (!mes) return this.ultimaPublicada(params, anio - 1, intentos - 1);
    const fecha = `${anio}-${String(mes.mes).padStart(2, '0')}-01`;
    return (await this.client.get('/api/v1/tariff/ubicacion/tarifa', { params: { ...params, fecha } })).data;
  }
}

export default TariffService;
