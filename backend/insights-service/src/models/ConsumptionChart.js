/**
 * Modelo para el gráfico de consumo vs predicción
 */
class ConsumptionChart {
  constructor({
    date,
    timezone,
    granularity,
    maxKwhScale,
    hours,
    actualKwh,
    predictedKwh,
    currentHourLocal,
    tariffBands,
    predictionUnavailable = false
  }) {
    this.date = date;
    this.timezone = timezone;
    this.granularity = granularity;
    this.maxKwhScale = maxKwhScale;
    this.hours = hours;
    this.actualKwh = actualKwh;
    this.predictedKwh = predictedKwh;
    this.currentHourLocal = currentHourLocal;
    this.tariffBands = tariffBands;
    this.predictionUnavailable = predictionUnavailable;
  }

  static fromData(data) {
    return new ConsumptionChart(data);
  }

  validate() {
    const requiredFields = [
      'date', 'timezone', 'granularity', 'hours', 
      'actualKwh', 'currentHourLocal', 'tariffBands'
    ];
    
    for (const field of requiredFields) {
      if (this[field] === undefined || this[field] === null) {
        throw new Error(`Missing required field: ${field}`);
      }
    }
    
    // Validate arrays length
    if (this.hours.length !== 24 || this.actualKwh.length !== 24) {
      throw new Error('Hours and actualKwh arrays must have 24 elements');
    }
    
    if (this.predictedKwh && this.predictedKwh.length !== 24) {
      throw new Error('PredictedKwh array must have 24 elements');
    }
    
    return true;
  }

  toJSON() {
    const result = {
      date: this.date,
      timezone: this.timezone,
      granularity: this.granularity,
      maxKwhScale: this.maxKwhScale,
      hours: this.hours,
      actualKwh: this.actualKwh,
      currentHourLocal: this.currentHourLocal,
      tariffBands: this.tariffBands
    };
    
    if (this.predictedKwh) {
      result.predictedKwh = this.predictedKwh;
    }
    
    if (this.predictionUnavailable) {
      result.predictionUnavailable = this.predictionUnavailable;
    }
    
    return result;
  }
}

export default ConsumptionChart;

// Export nombrado (funciones individuales)
export const {
  fromData
} = ConsumptionChart;