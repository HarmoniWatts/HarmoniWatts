const config = require('../config');

class TariffUtils {
  static getTariffByHour(hour, tariffBands = config.tariffBands) {
    const band = tariffBands.find(b => hour >= b.startHour && hour < b.endHour);
    return band || tariffBands[0];
  }

  static getNextHighTariffWindow(currentHour, tariffBands = config.tariffBands) {
    // Encontrar la siguiente franja PUNTA
    const puntaBands = tariffBands.filter(b => b.type === 'PUNTA');
    
    for (const band of puntaBands) {
      if (currentHour < band.startHour) {
        return {
          ...band,
          startsAtHour: band.startHour,
          endsAtHour: band.endHour
        };
      }
    }
    
    // Si no hay más franjas hoy, tomar la primera de mañana
    const nextBand = puntaBands[0];
    return {
      ...nextBand,
      startsAtHour: nextBand.startHour,
      endsAtHour: nextBand.endHour,
      isTomorrow: true
    };
  }

  static calculateEstimatedCost(consumptionKwh, tariffBands, actualSeries) {
    let totalCost = 0;
    
    for (let hour = 0; hour < 24; hour++) {
      const tariff = this.getTariffByHour(hour, tariffBands);
      const consumption = actualSeries[hour] || 0;
      totalCost += consumption * tariff.price;
    }
    
    return Math.round(totalCost);
  }

  static calculateSavings(consumptionKwh, tariffBands, baselineTariff = 520) {
    // Simplificación: ahorro comparando con tarifa media
    let savings = 0;
    
    for (let hour = 0; hour < 24; hour++) {
      const tariff = this.getTariffByHour(hour, tariffBands);
      const consumption = consumptionKwh[hour] || 0;
      const baselineCost = consumption * baselineTariff;
      const actualCost = consumption * tariff.price;
      savings += (baselineCost - actualCost);
    }
    
    return Math.max(0, Math.round(savings));
  }
}

module.exports = TariffUtils;