/**
 * Modelo para el resumen del dashboard (KPIs)
 */
class DashboardSummary {
  constructor({
    date,
    timezone,
    consumptionTodayKwh,
    consumptionVsYesterdayPercent,
    estimatedCostTodayCop,
    currentTariffSlot,
    savingsAccumulatedCop,
    savingsPeriod,
    nextHighTariffWindow
  }) {
    this.date = date;
    this.timezone = timezone;
    this.consumptionTodayKwh = consumptionTodayKwh;
    this.consumptionVsYesterdayPercent = consumptionVsYesterdayPercent;
    this.estimatedCostTodayCop = estimatedCostTodayCop;
    this.currentTariffSlot = currentTariffSlot;
    this.savingsAccumulatedCop = savingsAccumulatedCop;
    this.savingsPeriod = savingsPeriod;
    this.nextHighTariffWindow = nextHighTariffWindow;
  }

  static fromData(data) {
    return new DashboardSummary(data);
  }

  validate() {
    const requiredFields = [
      'date', 'timezone', 'consumptionTodayKwh', 
      'consumptionVsYesterdayPercent', 'estimatedCostTodayCop',
      'currentTariffSlot', 'savingsAccumulatedCop', 'savingsPeriod'
    ];
    
    for (const field of requiredFields) {
      if (this[field] === undefined || this[field] === null) {
        throw new Error(`Missing required field: ${field}`);
      }
    }
    
    return true;
  }

  toJSON() {
    return {
      date: this.date,
      timezone: this.timezone,
      consumptionTodayKwh: this.consumptionTodayKwh,
      consumptionVsYesterdayPercent: this.consumptionVsYesterdayPercent,
      estimatedCostTodayCop: this.estimatedCostTodayCop,
      currentTariffSlot: this.currentTariffSlot,
      savingsAccumulatedCop: this.savingsAccumulatedCop,
      savingsPeriod: this.savingsPeriod,
      nextHighTariffWindow: this.nextHighTariffWindow
    };
  }
}

export default DashboardSummary;

// Export nombrado (funciones individuales)
export const {
  fromData
} = DashboardSummary;