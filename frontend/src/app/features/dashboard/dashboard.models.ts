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
  predictedKwh: number[] | null;
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
  householdId?: string;
}
