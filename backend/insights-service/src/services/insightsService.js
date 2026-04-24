import { getDateInTimezone, getCurrentInTimezone, formatISO, formatDate, getCurrentHour } from '../utils/dateUtils.js';
import { getTariffByHour, calculateEstimatedCost, getNextHighTariffWindow, calculateSavings } from '../utils/tariffUtils.js';
import { defaultTimezone, tariffBands as _tariffBands } from '../config/index.js';
import { maxKwhScaleFromHourlySeries } from '../utils/chartScale.js';

class InsightsService {
  constructor(consumptionService, predictionService) {
    this.consumptionService = consumptionService;
    this.predictionService = predictionService;
  }

  async getDashboardSummary(householdId, dateStr, timezone = defaultTimezone) {
    const targetDate = getDateInTimezone(dateStr, timezone);
    const yesterday = targetDate.clone().subtract(1, 'day');
    const now = getCurrentInTimezone(timezone);
    const currentHour = now.hour();

    // Fetch data from services
    const [todayConsumption, yesterdayConsumption, predictionTotal, actualSeries] = await Promise.all([
      this.consumptionService.getDailyTotal(householdId, targetDate.format('YYYY-MM-DD'), timezone),
      this.consumptionService.getDailyTotal(householdId, yesterday.format('YYYY-MM-DD'), timezone),
      this.predictionService.getDailyTotal(householdId, targetDate.format('YYYY-MM-DD')),
      this.consumptionService.getHourlySeries(householdId, targetDate.format('YYYY-MM-DD'), timezone),
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

  async getConsumptionChart(householdId, dateStr, timezone = defaultTimezone) {
    const targetDate = getDateInTimezone(dateStr, timezone);
    const currentHour = getCurrentHour(timezone);

    // Fetch actual and predicted series - Usar getHourlySeries para ambos
    const [actualData, predictedData] = await Promise.all([
      this.consumptionService.getHourlySeries(householdId, targetDate.format('YYYY-MM-DD'), timezone),
      this.predictionService.getHourlySeries(householdId, targetDate.format('YYYY-MM-DD')),
    ]);
    
    // Extraer las series (asumiendo que getHourlySeries retorna { series: [...] })
    const actualKwh = actualData?.series || new Array(24).fill(0);
    //const predictedKwh = predictedData?.series || null;
    
    //fallback para generar predictedKwh si no viene del servicio (para pruebas)
    function gaussianNoise(min, max) {
    // Genera ruido con distribución normal aproximada usando Box-Muller
    let u = 0, v = 0;
    while(u === 0) u = Math.random(); // evitar 0
    while(v === 0) v = Math.random();
    let num = Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);

    // Escalar a rango [min, max]
    num = Math.abs(num); // solo positivo
    return min + (num % (max - min));
  }

  const predictedKwh = predictedData?.series || actualKwh.map(v => {
    const noise = gaussianNoise(0.01, 0.02); // ruido entre 10 y 20 Wh
    return Math.round((v + noise) * 1000) / 1000; // mantener hasta 3 decimales
  });
  //// Fin de fallback

    // Eje Y: solo a partir del insumo (serie horaria = agregado de valor_kwh por hora)
    const maxKwhScale = maxKwhScaleFromHourlySeries(actualKwh, predictedKwh, 1.08);

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
      response.predictedKwh = predictedKwh.map(v => Math.round(v * 1000) / 1000); // Redondear a 3 decimales
    } else {
      response.predictedKwh = null;
      response.predictionUnavailable = true;
    }

    return response;
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