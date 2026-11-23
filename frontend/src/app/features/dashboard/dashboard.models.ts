/** Contratos alineados con HarmoniWatts/docs/DASHBOARD-API.md */

export type TariffType = 'VALLE' | 'MEDIA' | 'PUNTA' | string;

export interface DashboardApiEndpoints {
  /** GET — KPIs del día + próxima franja cara */
  summaryPath: string;
  /** GET — series horarias + franjas del gráfico */
  consumptionChartPath: string;
  /** GET — lista de recomendaciones IA */
  recommendationsPath: string;
  /** GET — top electrodomésticos */
  appliancesTopPath: string;
  /** POST — `{id}` será sustituido por el id del ítem */
  recommendationApplyPathTemplate: string;
  /** POST — `{id}` será sustituido por el id del ítem */
  recommendationDismissPathTemplate: string;
}

export interface DashboardSummaryResponse {
  date: string;
  timezone: string;
  consumptionTodayKwh: number;
  consumptionVsYesterdayPercent: number;
  estimatedCostTodayCop: number;
  currentTariffSlot: {
    type: TariffType;
    label: string;
    energyPriceCopPerKwh: number;
  };
  savingsAccumulatedCop: number;
  savingsPeriod: {
    label: string;
    from: string;
    to: string;
  };
  nextHighTariffWindow: {
    type: TariffType;
    label: string;
    startsAt: string;
    endsAt: string;
    displayHint?: string;
  };
}

export interface TariffBand {
  type: TariffType;
  startHour: number;
  endHour: number;
  energyPriceCopPerKwh: number;
}

export interface DashboardConsumptionChartResponse {
  date: string;
  timezone: string;
  granularity: string;
  maxKwhScale?: number;
  hours: number[];
  actualKwh: number[];
  /** Predicción del modelo por hora; null en las horas sin predicción. */
  predictedKwh: (number | null)[] | null;
  currentHourLocal: number;
  tariffBands: TariffBand[];
  predictionUnavailable?: boolean;
}

export interface RecommendationItem {
  id: string;
  title: string;
  body: string;
  suggestedStart?: string;
  estimatedSavingsCop?: number;
  priority?: number;
}

export interface DashboardRecommendationsResponse {
  date: string;
  items: RecommendationItem[];
}

export interface ApplianceTopItem {
  id: string;
  name: string;
  category: string;
  sharePercent: number;
  consumptionKwh?: number;
}

export interface DashboardAppliancesTopResponse {
  date: string;
  metric: string;
  items: ApplianceTopItem[];
}

export interface DashboardQueryParams {
  date?: string;
  /** Contrato de la vivienda seleccionada con su comercializadora. */
  noContrato?: string;
  codComercializadora?: string;
}

// ---------------------------------------------------------------- HAR-25: predicción
export type PredictionConfidenceLevel = 'HIGH' | 'MEDIUM' | 'LOW';

export interface PredictionConfidence {
  level: PredictionConfidenceLevel;
  /** Error porcentual (WAPE) de los totales de 24 h en los días evaluados. */
  dailyErrorPct: number | null;
  hourlyErrorPct: number | null;
  daysEvaluated: number;
  hoursEvaluated: number;
  method: string | null;
}

/** Hora pasada: predicción del modelo hecha sin ver ese día vs consumo real. */
export interface PredictionHistoryPoint {
  timestamp: string;
  actualKwh: number;
  predictedKwh: number;
}

/** Hora futura con su rango. */
export interface PredictionForecastPoint {
  timestamp: string;
  predictedKwh: number;
  lowerKwh: number;
  upperKwh: number;
}

export interface DashboardPredictionResponse {
  available: boolean;
  reason?: string;
  message?: string;
  meterNo?: string;
  generatedAt?: string;
  lastReading?: string;
  model?: string | null;
  confidence?: PredictionConfidence;
  history?: PredictionHistoryPoint[];
  forecast?: PredictionForecastPoint[];
}

// ---------------------------------------------------------------- HAR-21: alertas
export type AlertSeverity = 'LOW' | 'MEDIUM' | 'HIGH';
export type AlertType = 'TARIFF_PEAK' | 'TARIFF_PEAK_SOON' | 'CONSUMPTION_HOUR' | 'CONSUMPTION_DAY';

export interface DashboardAlert {
  /** Estable para la misma situación: sirve para marcarla como leída. */
  id: string;
  type: AlertType;
  severity: AlertSeverity;
  title: string;
  message: string;
  /** Hora local 'YYYY-MM-DDTHH:mm[:ss]'. */
  timestamp: string;
  data?: Record<string, unknown>;
}

export interface DashboardAlertsResponse {
  generatedAt: string;
  timezone: string;
  alerts: DashboardAlert[];
  sources: { tariff: string; consumption: string };
}

export interface AlertsQueryParams {
  noContrato?: string;
  codComercializadora?: string;
  idZona?: number;
  codMercado?: string;
  estrato?: number;
  /** Hora simulada 'YYYY-MM-DDTHH:mm' (solo pruebas en desarrollo). */
  at?: string;
}
