const DateUtils = require('../utils/dateUtils');
const TariffUtils = require('../utils/tariffUtils');
const config = require('../config');

class InsightsService {
  constructor(consumptionService, predictionService) {
    this.consumptionService = consumptionService;
    this.predictionService = predictionService;
  }

  async getDashboardSummary(householdId, dateStr, timezone = config.defaultTimezone) {
    const targetDate = DateUtils.getDateInTimezone(dateStr, timezone);
    const yesterday = targetDate.clone().subtract(1, 'day');
    const now = DateUtils.getCurrentInTimezone(timezone);
    const currentHour = now.hour();

    // Fetch data from services
    const [todayConsumption, yesterdayConsumption, predictionTotal] = await Promise.all([
      this.consumptionService.getDailyTotal(householdId, targetDate.format('YYYY-MM-DD')),
      this.consumptionService.getDailyTotal(householdId, yesterday.format('YYYY-MM-DD')),
      this.predictionService.getDailyTotal(householdId, targetDate.format('YYYY-MM-DD'))
    ]);

    // Calculate consumption vs yesterday
    const consumptionTodayKwh = todayConsumption?.totalKwh || 0;
    const consumptionYesterdayKwh = yesterdayConsumption?.totalKwh || 0;
    let consumptionVsYesterdayPercent = 0;
    
    if (consumptionYesterdayKwh > 0) {
      consumptionVsYesterdayPercent = ((consumptionTodayKwh - consumptionYesterdayKwh) / consumptionYesterdayKwh) * 100;
    }

    // Get current tariff slot
    const currentTariff = TariffUtils.getTariffByHour(currentHour);
    
    // Calculate estimated cost (need actual series for accurate calculation)
    const actualSeries = await this.consumptionService.getDailySeries(householdId, targetDate.format('YYYY-MM-DD'));
    const estimatedCost = TariffUtils.calculateEstimatedCost(
      consumptionTodayKwh,
      config.tariffBands,
      actualSeries?.series || new Array(24).fill(0)
    );

    // Get next high tariff window
    const nextHighTariff = TariffUtils.getNextHighTariffWindow(currentHour);
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
        startsAt: DateUtils.formatISO(startDateTime, timezone),
        endsAt: DateUtils.formatISO(endDateTime, timezone),
        displayHint: this.formatTimeHint(minutesDiff)
      };
    }

    // Calculate savings (simplified)
    const savingsAccumulated = TariffUtils.calculateSavings(
      actualSeries?.series || new Array(24).fill(0),
      config.tariffBands
    );

    // Get month range
    const monthStart = targetDate.clone().startOf('month');
    const monthEnd = targetDate.clone().endOf('month');

    return {
      date: DateUtils.formatDate(targetDate, timezone),
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

  async getConsumptionChart(householdId, dateStr, timezone = config.defaultTimezone) {
    const targetDate = DateUtils.getDateInTimezone(dateStr, timezone);
    const currentHour = DateUtils.getCurrentHour(timezone);

    // Fetch actual and predicted series
    const [actualData, predictedData] = await Promise.all([
      this.consumptionService.getDailySeries(householdId, targetDate.format('YYYY-MM-DD')),
      this.predictionService.getDailySeries(householdId, targetDate.format('YYYY-MM-DD'))
    ]);

    const actualKwh = actualData?.series || new Array(24).fill(0);
    const predictedKwh = predictedData?.series || null;
    
    // Calculate max scale
    const maxActual = Math.max(...actualKwh);
    const maxPredicted = predictedKwh ? Math.max(...predictedKwh) : 0;
    const maxKwhScale = Math.ceil(Math.max(maxActual, maxPredicted) * 1.2);

    // Prepare tariff bands for the chart
    const tariffBands = config.tariffBands.map(band => ({
      type: band.type,
      startHour: band.startHour,
      endHour: band.endHour,
      energyPriceCopPerKwh: band.price
    }));

    const response = {
      date: DateUtils.formatDate(targetDate, timezone),
      timezone: timezone,
      granularity: "HOUR",
      maxKwhScale: maxKwhScale,
      hours: Array.from({ length: 24 }, (_, i) => i),
      actualKwh: actualKwh.map(v => Math.round(v * 10) / 10),
      currentHourLocal: currentHour,
      tariffBands: tariffBands
    };

    if (predictedKwh) {
      response.predictedKwh = predictedKwh.map(v => Math.round(v * 10) / 10);
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

module.exports = InsightsService;