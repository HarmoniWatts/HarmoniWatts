import pkg from 'moment-timezone';
import { defaultTimezone } from '../config/index.js';
import { alertasConsumo, alertasFranja, ordenarAlertas, UMBRALES_CONSUMO, MINUTOS_PUNTA_PRONTO } from '../utils/alertas.js';

const { tz, utc } = pkg;

/** Historia para el promedio: 4 semanas + hoy. */
const HORAS_HISTORIA = 29 * 24;

/**
 * Alertas visuales del dashboard (HAR-21): franja de alto precio (tarifa real de la vivienda)
 * y consumo por encima de lo habitual (lecturas del contrato).
 */
class AlertsService {
  constructor(consumptionService, tariffService) {
    this.consumptionService = consumptionService;
    this.tariffService = tariffService;
  }

  /**
   * @param contrato { noContrato, codComercializadora } | null
   * @param ubicacion { idZona, codMercado, estrato } | null
   */
  async getAlerts(contrato, ubicacion, timezone = defaultTimezone, at = null) {
    // `at` (opcional, pruebas/QA): hora simulada 'YYYY-MM-DDTHH:mm' en la zona horaria
    const now = at ? tz(at, timezone) : tz(timezone);
    const ahora = { fecha: now.format('YYYY-MM-DD'), hora: now.hour(), minuto: now.minute() };
    const fuentes = { tariff: 'SKIPPED', consumption: 'SKIPPED' };

    const [franja, consumo] = await Promise.all([
      ubicacion
        ? this.tariffService
            .getPreciosVigentes(ubicacion, ahora.fecha)
            .then((precios) => {
              fuentes.tariff = precios ? 'OK' : 'NO_TARIFF';
              return precios ? alertasFranja(precios, ahora) : [];
            })
            .catch((e) => {
              console.error('Alertas: tarifa no disponible:', e.message);
              fuentes.tariff = 'ERROR';
              return [];
            })
        : [],
      contrato
        ? this.consumptionService
            .getRawSeries(contrato, HORAS_HISTORIA)
            .then((data) => {
              // consumption-service entrega UTC sin zona → hora local
              const lecturas = data.map((d) => ({
                ts: utc(d.timestamp).tz(timezone).format('YYYY-MM-DDTHH:mm:ss'),
                kwh: Number(d.kwh),
              }));
              fuentes.consumption = lecturas.length ? 'OK' : 'NO_READINGS';
              return alertasConsumo(lecturas);
            })
            .catch((e) => {
              console.error('Alertas: consumos no disponibles:', e.message);
              fuentes.consumption = 'ERROR';
              return [];
            })
        : [],
    ]);

    return {
      generatedAt: now.format(),
      timezone,
      alerts: ordenarAlertas([...franja, ...consumo]),
      sources: fuentes,
      rules: {
        consumptionExcessPct: Object.fromEntries(UMBRALES_CONSUMO.map((u) => [u.severidad, Math.round(u.min * 100)])),
        peakSoonMinutes: MINUTOS_PUNTA_PRONTO,
      },
    };
  }
}

export default AlertsService;
