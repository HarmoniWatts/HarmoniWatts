import { getDateInTimezone, getCurrentInTimezone, formatISO, formatDate, getCurrentHour } from '../utils/dateUtils.js';
import { getTariffByHour, calculateEstimatedCost, getNextHighTariffWindow, calculateSavings } from '../utils/tariffUtils.js';
import { defaultTimezone, tariffBands as _tariffBands } from '../config/index.js';
import { maxKwhScaleFromHourlySeries } from '../utils/chartScale.js';
import { seriePrediccionDelDia, toDashboardPrediction } from '../utils/prediccion.js';

class InsightsService {
  constructor(consumptionService, predictionService) {
    this.consumptionService = consumptionService;
    this.predictionService = predictionService;
  }

  async getDashboardSummary(contrato, dateStr, timezone = defaultTimezone) {
    const targetDate = getDateInTimezone(dateStr, timezone);
    const yesterday = targetDate.clone().subtract(1, 'day');
    const now = getCurrentInTimezone(timezone);
    const currentHour = now.hour();

    // Fetch data from services
    const [todayConsumption, yesterdayConsumption, predictionTotal, actualSeries] = await Promise.all([
      this.consumptionService.getDailyTotal(contrato, targetDate.format('YYYY-MM-DD'), timezone),
      this.consumptionService.getDailyTotal(contrato, yesterday.format('YYYY-MM-DD'), timezone),
      this.predictionService.getDailyTotal(contrato, targetDate.format('YYYY-MM-DD')),
      this.consumptionService.getHourlySeries(contrato, targetDate.format('YYYY-MM-DD'), timezone),
    ]);

    // Calculate consumption vs yesterday (contrato FastAPI: total_consumption_kwh)
    const consumptionTodayKwh = todayConsumption?.total_consumption_kwh ?? todayConsumption?.totalKwh ?? 0;
    const consumptionYesterdayKwh =
      yesterdayConsumption?.total_consumption_kwh ?? yesterdayConsumption?.totalKwh ?? 0;
    let consumptionVsYesterdayPercent = 0;
    
    if (consumptionYesterdayKwh > 0) {
      consumptionVsYesterdayPercent = ((consumptionTodayKwh - consumptionYesterdayKwh) / consumptionYesterdayKwh) * 100;
    }

    // Get current tariff slot
    const currentTariff = getTariffByHour(currentHour);
    
    // Calculate estimated cost
    const estimatedCost = calculateEstimatedCost(
      consumptionTodayKwh,
      _tariffBands,
      actualSeries?.series || new Array(24).fill(0)
    );

    // Get next high tariff window
    const nextHighTariff = getNextHighTariffWindow(currentHour);
    let nextHighTariffWindow = null;
    
    if (nextHighTariff) {
      const startDateTime = targetDate.clone().hour(nextHighTariff.startsAtHour);
      if (nextHighTariff.isTomorrow) {
        startDateTime.add(1, 'day');
      }
      
      const endDateTime = startDateTime.clone().hour(nextHighTariff.endsAtHour);
      const minutesDiff = Math.round(startDateTime.diff(now, 'minutes'));
      
      nextHighTariffWindow = {
        type: nextHighTariff.type,
        label: nextHighTariff.label,
        startsAt: formatISO(startDateTime, timezone),
        endsAt: formatISO(endDateTime, timezone),
        displayHint: this.formatTimeHint(minutesDiff)
      };
    }

    // Calculate savings
    const savingsAccumulated = calculateSavings(
      actualSeries?.series || new Array(24).fill(0),
      _tariffBands
    );

    // Get month range
    const monthStart = targetDate.clone().startOf('month');
    const monthEnd = targetDate.clone().endOf('month');

    return {
      date: formatDate(targetDate, timezone),
      timezone: timezone,
      consumptionTodayKwh: Math.round(consumptionTodayKwh * 10) / 10,
      consumptionVsYesterdayPercent: Math.round(consumptionVsYesterdayPercent * 10) / 10,
      estimatedCostTodayCop: estimatedCost,
      currentTariffSlot: {
        type: currentTariff.type,
        label: currentTariff.label,
        energyPriceCopPerKwh: currentTariff.price
      },
      savingsAccumulatedCop: savingsAccumulated,
      savingsPeriod: {
        label: "Este mes",
        from: monthStart.format('YYYY-MM-DD'),
        to: monthEnd.format('YYYY-MM-DD')
      },
      nextHighTariffWindow
    };
  }

  async getConsumptionChart(contrato, dateStr, timezone = defaultTimezone) {
    const targetDate = getDateInTimezone(dateStr, timezone);
    const currentHour = getCurrentHour(timezone);

    // Consumo real del día y pronóstico del modelo (prediction-service, HAR-25)
    const fecha = targetDate.format('YYYY-MM-DD');
    const [actualData, pronostico] = await Promise.all([
      this.consumptionService.getHourlySeries(contrato, fecha, timezone),
      this.predictionService.getPronosticoSeguro(contrato),
    ]);

    const actualKwh = actualData?.series || new Array(24).fill(0);
    // Predicción del modelo para las horas de ese día (null donde no hay); ya no se simula
    const predictedKwh = seriePrediccionDelDia(pronostico, fecha);

    // Eje Y: solo a partir del insumo (serie horaria = agregado de valor_kwh por hora)
    const maxKwhScale = maxKwhScaleFromHourlySeries(actualKwh, (predictedKwh ?? []).filter((v) => v != null), 1.08);

    // Prepare tariff bands for the chart (solo las bandas del día)
    const tariffBands = _tariffBands.map(band => ({
      type: band.type,
      startHour: band.startHour,
      endHour: band.endHour,
      energyPriceCopPerKwh: band.price
    }));

    // Construir respuesta según el contrato
    const response = {
      date: formatDate(targetDate, timezone),
      timezone: timezone,
      granularity: "HOUR",
      ...(maxKwhScale != null ? { maxKwhScale } : {}),
      hours: Array.from({ length: 24 }, (_, i) => i),
      actualKwh: actualKwh.map(v => Math.round(v * 1000) / 1000), // Redondear a 3 decimales
      currentHourLocal: currentHour,
      tariffBands: tariffBands
    };

    // Agregar predictedKwh solo si está disponible
    if (predictedKwh) {
      response.predictedKwh = predictedKwh;
    } else {
      response.predictedKwh = null;
      response.predictionUnavailable = true;
    }

    return response;
  }


  /**
   * Predicción vs real de los últimos días, próximos días y confianza (HAR-25).
   * Si el contrato no tiene historia suficiente responde available=false con el motivo.
   */
  async getPrediction(contrato, { diasPasados = 7, diasFuturos = 7 } = {}) {
    try {
      const p = await this.predictionService.getPronostico(contrato, { diasPasados, diasFuturos });
      return toDashboardPrediction(p);
    } catch (error) {
      if (error.response?.status === 404) {
        return {
          available: false,
          reason: 'INSUFFICIENT_HISTORY',
          message: error.response.data?.detail ?? 'Historia de consumo insuficiente para predecir',
        };
      }
      throw error;
    }
  }

  formatTimeHint(minutesDiff) {
    if (minutesDiff <= 0) return "Ahora";
    if (minutesDiff < 60) return `Punta en ${minutesDiff} min`;
    const hours = Math.floor(minutesDiff / 60);
    const mins = minutesDiff % 60;
    if (mins === 0) return `Punta en ${hours}h`;
    return `Punta en ${hours}h ${mins}min`;
  }
}

export default InsightsService;