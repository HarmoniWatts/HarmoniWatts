import { CommonModule } from '@angular/common';
import { Component, computed, DestroyRef, effect, inject, OnInit, signal, untracked } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { forkJoin, of } from 'rxjs';
import { catchError, finalize } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { DashboardService } from './dashboard.service';
import {
  estimateDailyCostCop,
  toCurrentTariffSlot,
  toNextHighTariffWindow,
  toTariffBands,
} from '../tarifas/tariff-dashboard.adapter';
import type { TarifaUbicacionResponse } from '../tarifas/tarifas.models';
import { TarifasService } from '../tarifas/tarifas.service';
import { ViviendaContextService } from '../vivienda/vivienda-context.service';
import { ViviendaSelectorComponent } from '../vivienda/vivienda-selector.component';
import { InfoTipComponent } from '../../shared/components/info-tip';
import { GLOSARIO } from '../tarifas/tarifas-glosario';
import { smoothPathLine } from './dashboard-chart.util';
import type {
  DashboardAppliancesTopResponse,
  DashboardConsumptionChartResponse,
  DashboardRecommendationsResponse,
  DashboardSummaryResponse,
  TariffBand,
  TariffType,
} from './dashboard.models';

const CHART_INNER_WIDTH = 1000;
const CHART_HEIGHT = 300;
const CHART_PAD = { left: 58, right: 10, top: 10, bottom: 32 } as const;

export interface ChartViewModel {
  chartInnerWidth: number;
  chartHeight: number;
  chartPad: typeof CHART_PAD;
  plotW: number;
  plotH: number;
  maxKwh: number;
  hours: number[];
  actual: number[];
  predicted: number[] | null;
  predictionUnavailable: boolean;
  /** Hora actual y su posición; null si la fecha consultada no es hoy (sin cursor "ahora"). */
  currentHour: number | null;
  currentHourX: number | null;
  hourLabels: { hour: number; x: number; isCurrent: boolean }[];
  tariffRects: { x: number; width: number; color: string }[];
  yTicks: { value: number; y: number; label: string }[];
  realLinePath: string;
  predLinePath: string;
  realAreaPath: string;
  realPoints: { x: number; y: number; isCurrent: boolean }[];
  baselineY: number;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, ViviendaSelectorComponent, InfoTipComponent],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css',
})
export class DashboardComponent implements OnInit {
  private readonly dashboardApi = inject(DashboardService);
  private readonly tarifasApi = inject(TarifasService);
  private readonly viviendaCtx = inject(ViviendaContextService);
  private readonly destroyRef = inject(DestroyRef);

  /** Textos de los botones informativos. */
  readonly g = GLOSARIO;

  readonly loading = signal(true);
  readonly selectedDate = signal(this.todayYmd());
  /** Solo el día actual tiene "ahora": cursor, hora resaltada y franja vigente. */
  readonly isToday = computed(() => this.selectedDate() === this.todayYmd());
  /** Hora de referencia para la tarifa de un día que no es hoy. */
  readonly referenceHour = 12;

  summary: DashboardSummaryResponse | null = null;
  chart: DashboardConsumptionChartResponse | null = null;
  recommendations: DashboardRecommendationsResponse | null = null;
  appliances: DashboardAppliancesTopResponse | null = null;

  chartVm: ChartViewModel | null = null;

  /** Respuestas de insights-service sin adaptar; las tarifas reales se aplican encima. */
  private insightsSummary: DashboardSummaryResponse | null = null;
  private insightsChart: DashboardConsumptionChartResponse | null = null;
  private tarifa: TarifaUbicacionResponse | null = null;
  /** Descripción de la tarifa aplicada o motivo por el que no hay tarifa. */
  readonly tariffNote = signal<string | null>(null);
  /**
   * Hay tarifa publicada para la vivienda y la fecha. Si no, no se muestran franjas,
   * precios ni costo (los valores de ejemplo de insights-service no se usan).
   */
  readonly tariffAvailable = signal(false);

  constructor() {
    // Cambiar de vivienda solo recarga las tarifas
    effect(() => {
      this.viviendaCtx.ubicacion();
      untracked(() => this.loadTarifa());
    });
  }

  readonly loadError = signal<string | null>(null);
  readonly sectionError = signal<{ summary?: boolean; chart?: boolean; reco?: boolean; appliances?: boolean }>({});

  readonly actionBusyId = signal<string | null>(null);

  ngOnInit(): void {
    this.loadAll();
  }

  onDateChange(value: string): void {
    if (value) {
      this.selectedDate.set(value);
      this.loadAll();
    }
  }

  reload(): void {
    this.loadAll();
  }

  absNumber(n: number): number {
    return Math.abs(n);
  }

  formatCop(value: number | undefined): string {
    if (value == null || Number.isNaN(value)) {
      return '—';
    }
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      maximumFractionDigits: 0,
    }).format(value);
  }

  tariffBandUiColor(type: TariffType): { bg: string; fg: string } {
    const t = String(type).toUpperCase();
    if (t === 'VALLE') {
      return {
        bg: 'var(--color-tariff-valle-bg)',
        fg: 'var(--color-tariff-valle-fg)',
      };
    }
    if (t === 'PUNTA') {
      return {
        bg: 'var(--color-tariff-punta-bg)',
        fg: 'var(--color-tariff-punta-fg)',
      };
    }
    return {
      bg: 'var(--color-tariff-llano-bg)',
      fg: 'var(--color-tariff-llano-fg)',
    };
  }

  /**
   * Color para los rectángulos de fondo en el chart (sobre fondo más oscuro).
   * Mantenemos tonos algo más bajos que las píldoras para no saturar.
   */
  tariffChartColor(type: TariffType): string {
    const t = String(type).toUpperCase();
    if (t === 'VALLE') {
      return '#1d8f52';
    }
    if (t === 'PUNTA') {
      return '#c53030';
    }
    return '#b45309';
  }

  applianceIconKind(category: string): 'heat' | 'washer' | 'hvac' | 'fridge' | 'light' | 'other' {
    const c = category.toUpperCase();
    if (c.includes('WATER') || c.includes('HEATER') || c.includes('CALENT')) {
      return 'heat';
    }
    if (c.includes('WASHER') || c.includes('LAVAD')) {
      return 'washer';
    }
    if (c.includes('AIR') || c.includes('HVAC') || c.includes('AC')) {
      return 'hvac';
    }
    if (c.includes('FRIDGE') || c.includes('REFR') || c.includes('NEVER')) {
      return 'fridge';
    }
    if (c.includes('LIGHT') || c.includes('LAMP')) {
      return 'light';
    }
    return 'other';
  }

  barGradient(share: number): string {
    if (share >= 75) {
      return 'linear-gradient(90deg, #f97316, #ef4444)';
    }
    if (share >= 55) {
      return 'linear-gradient(90deg, #22d3ee, #f59e0b)';
    }
    return 'linear-gradient(90deg, #38bdf8, #eab308)';
  }

  sortedBands(bands: TariffBand[] | undefined): TariffBand[] {
    if (!bands?.length) {
      return [];
    }
    return [...bands].sort((a, b) => a.startHour - b.startHour);
  }

  activeBandIndex(bands: TariffBand[], hour: number): number {
    return bands.findIndex((b) => hour >= b.startHour && hour < b.endHour);
  }

  formatTariffType(type: TariffType): string {
    const raw = String(type).replace(/_/g, ' ').toLowerCase();
    return raw.replace(/\b\w/g, (c) => c.toUpperCase());
  }

  franjaRows(chart: DashboardConsumptionChartResponse): { band: TariffBand; rowIdx: number; activeIdx: number }[] {
    const bands = this.sortedBands(chart.tariffBands);
    const activeIdx = this.isToday() ? this.activeBandIndex(bands, chart.currentHourLocal) : -1;
    return bands.map((band, rowIdx) => ({ band, rowIdx, activeIdx }));
  }

  formatWindowRange(startsAt: string, endsAt: string): string {
    try {
      const s = new Date(startsAt);
      const e = new Date(endsAt);
      const tf = new Intl.DateTimeFormat('es-CO', { hour: '2-digit', minute: '2-digit', hour12: false });
      return `${tf.format(s)} – ${tf.format(e)}`;
    } catch {
      return '';
    }
  }

  applyRecommendation(id: string): void {
    this.actionBusyId.set(id);
    this.dashboardApi
      .applyRecommendation(id)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.actionBusyId.set(null)),
      )
      .subscribe({
        next: () => this.removeRecommendation(id),
        error: () => this.loadError.set('No se pudo aplicar la recomendación.'),
      });
  }

  dismissRecommendation(id: string): void {
    this.actionBusyId.set(id);
    this.dashboardApi
      .dismissRecommendation(id)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.actionBusyId.set(null)),
      )
      .subscribe({
        next: () => this.removeRecommendation(id),
        error: () => this.loadError.set('No se pudo ignorar la recomendación.'),
      });
  }

  private removeRecommendation(id: string): void {
    if (!this.recommendations) {
      return;
    }
    this.recommendations = {
      ...this.recommendations,
      items: this.recommendations.items.filter((i) => i.id !== id),
    };
  }

  private todayYmd(): string {
    const d = new Date();
    const p = (n: number) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
  }

  /** Tarifa de la vivienda activa para la fecha seleccionada (tariff-service). */
  private loadTarifa(): void {
    const ubicacion = this.viviendaCtx.ubicacion();
    if (!ubicacion) {
      this.tarifa = null;
      this.tariffNote.set(
        this.viviendaCtx.selected()
          ? 'Sin tarifas: la vivienda no tiene ciudad configurada en Mi vivienda.'
          : 'Sin tarifas: registra una vivienda con su ciudad y estrato.',
      );
      this.applyTarifa();
      return;
    }
    this.tarifasApi
      .getTarifa(ubicacion, this.selectedDate())
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        catchError(() => of(null)),
      )
      .subscribe((t) => {
        this.tarifa = t;
        this.tariffNote.set(
          t
            ? `Tarifas de ${t.ciudad.municipio} · estrato ${t.seleccion.estrato} · tipo ${t.seleccion.cod_tipo_tarifa_aplicado}`
            : `Sin tarifas: la comercializadora aún no ha publicado la tarifa de ${this.mesDeFecha(this.selectedDate())}.`,
        );
        this.applyTarifa();
      });
  }

  /**
   * Aplica el adaptador de tarifas sobre el resumen y el gráfico de insights.
   * Las franjas y precios salen solo de tariff-service; sin tarifa quedan vacíos.
   */
  private applyTarifa(): void {
    const t = this.tarifa;
    const chart = this.insightsChart;
    const summary = this.insightsSummary;
    this.tariffAvailable.set(t != null);

    this.chart = chart ? { ...chart, tariffBands: t ? toTariffBands(t.precios) : [] } : chart;
    this.chartVm = this.chart ? this.buildChartView(this.chart) : null;

    if (!summary || !t) {
      this.summary = summary;
      return;
    }
    // Otro día: tarifa de referencia a mediodía y primera punta del día (no "ahora")
    const today = this.isToday();
    const clockHour = today ? new Date().getHours() : this.referenceHour;
    this.summary = {
      ...summary,
      currentTariffSlot: toCurrentTariffSlot(t.precios, clockHour) ?? summary.currentTariffSlot,
      nextHighTariffWindow: toNextHighTariffWindow(t.precios, this.selectedDate(), today ? clockHour : 0) ?? {
        type: 'PUNTA',
        label: 'Sin punta',
        startsAt: '',
        endsAt: '',
        displayHint: today ? 'Sin punta pendiente hoy' : 'Sin franja punta',
      },
      estimatedCostTodayCop: chart
        ? estimateDailyCostCop(t.precios, chart.actualKwh ?? [], chart.hours)
        : summary.estimatedCostTodayCop,
    };
  }

  /** "15 sept 2026" para el título del gráfico. */
  fechaCorta(ymd: string): string {
    const [y, m, d] = ymd.split('-').map(Number);
    return new Intl.DateTimeFormat('es-CO', { day: 'numeric', month: 'short', year: 'numeric' }).format(
      new Date(y, m - 1, d),
    );
  }

  private mesDeFecha(ymd: string): string {
    const [y, m] = ymd.split('-').map(Number);
    const mes = new Intl.DateTimeFormat('es-CO', { month: 'long' }).format(new Date(y, m - 1, 1));
    return `${mes} ${y}`;
  }

  private loadAll(): void {
    this.loadTarifa();
    this.loading.set(true);
    this.loadError.set(null);
    this.sectionError.set({});

    const q = {
      date: this.selectedDate(),
      householdId: environment.defaultHouseholdId,
    };

    forkJoin({
      summary: this.dashboardApi.getSummary(q).pipe(
        catchError(() => {
          this.sectionError.update((e) => ({ ...e, summary: true }));
          return of(null);
        }),
      ),
      chart: this.dashboardApi.getConsumptionChart(q).pipe(
        catchError(() => {
          this.sectionError.update((e) => ({ ...e, chart: true }));
          return of(null);
        }),
      ),
      recommendations: this.dashboardApi.getRecommendations({ ...q, limit: 3 }).pipe(
        catchError(() => {
          this.sectionError.update((e) => ({ ...e, reco: true }));
          return of(null);
        }),
      ),
      appliances: this.dashboardApi.getAppliancesTop({ ...q, limit: 5 }).pipe(
        catchError(() => {
          this.sectionError.update((e) => ({ ...e, appliances: true }));
          return of(null);
        }),
      ),
    })
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: ({ summary, chart, recommendations, appliances }) => {
          this.insightsSummary = summary;
          this.insightsChart = chart;
          this.recommendations = recommendations;
          this.appliances = appliances;
          this.applyTarifa();
          const allFailed = !summary && !chart && !recommendations && !appliances;
          if (allFailed) {
            this.loadError.set('No se pudo cargar el dashboard. Revisa la API o la URL base.');
          }
        },
        error: () => {
          this.loadError.set('Error inesperado al cargar el dashboard.');
        },
      });
  }

  private buildChartView(chart: DashboardConsumptionChartResponse): ChartViewModel {
    const hours = chart.hours?.length ? chart.hours : Array.from({ length: chart.actualKwh.length }, (_, i) => i);
    const actual = chart.actualKwh ?? [];
    const predicted = chart.predictedKwh ?? null;
    const predictionUnavailable = chart.predictionUnavailable === true || predicted === null;

    // Eje Y solo desde el insumo (series horarias en kWh, agregado de valor_kwh en backend)
    const seriesValues = [...actual, ...(predicted ?? [])].filter((v) => Number.isFinite(v));
    const maxFromData = seriesValues.length ? Math.max(0, ...seriesValues) : 0;
    const maxKwh =
      maxFromData > 0 ? this.niceCeilKwh(maxFromData * 1.06) : this.chartEmptyAxisMaxKwh();

    const plotW = CHART_INNER_WIDTH - CHART_PAD.left - CHART_PAD.right;
    const plotH = CHART_HEIGHT - CHART_PAD.top - CHART_PAD.bottom;

    const xForClockHour = (hod: number) =>
      CHART_PAD.left + (Math.min(23, Math.max(0, hod)) / 23) * plotW;
    const xDayFrac = (t: number) => CHART_PAD.left + (t / 24) * plotW;
    const yForKwh = (val: number) => CHART_PAD.top + (1 - val / maxKwh) * plotH;
    const baselineY = CHART_HEIGHT - CHART_PAD.bottom;

    const n = Math.max(actual.length, predicted?.length ?? 0, hours.length, 1);
    const nowHour = this.isToday() ? Math.min(23, Math.max(0, chart.currentHourLocal)) : null;
    const realPoints: { x: number; y: number; isCurrent: boolean }[] = [];
    for (let idx = 0; idx < n; idx++) {
      const hodRaw = hours[idx];
      const hod = typeof hodRaw === 'number' ? hodRaw : idx;
      const v = actual[Math.min(idx, actual.length - 1)] ?? 0;
      realPoints.push({
        x: xForClockHour(hod),
        y: yForKwh(v),
        isCurrent: hod === nowHour,
      });
    }

    const predPoints: { x: number; y: number }[] = [];
    if (predicted && !predictionUnavailable) {
      for (let idx = 0; idx < n; idx++) {
        const hodRaw = hours[idx];
        const hod = typeof hodRaw === 'number' ? hodRaw : idx;
        const v = predicted[Math.min(idx, predicted.length - 1)] ?? 0;
        predPoints.push({ x: xForClockHour(hod), y: yForKwh(v) });
      }
    }

    const realLinePath = smoothPathLine(realPoints);
    const predLinePath = predPoints.length ? smoothPathLine(predPoints) : '';
    const realAreaPath =
      realPoints.length > 0
        ? `${realLinePath} L ${realPoints[realPoints.length - 1].x} ${baselineY} L ${realPoints[0].x} ${baselineY} Z`
        : '';

    const tariffRects = (chart.tariffBands ?? []).map((b) => ({
      x: xDayFrac(b.startHour),
      width: Math.max(0, xDayFrac(b.endHour) - xDayFrac(b.startHour)),
      color: this.tariffChartColor(b.type),
    }));

    const yTicks: { value: number; y: number; label: string }[] = [];
    for (let i = 0; i <= 5; i++) {
      const value = (maxKwh * (5 - i)) / 5;
      const y = CHART_PAD.top + (1 - value / maxKwh) * plotH;
      const label = this.formatYTickLabel(value, maxKwh);
      yTicks.push({ value, y, label });
    }

    const currentHourX = nowHour !== null ? xForClockHour(nowHour) : null;
    const hourLabels = Array.from({ length: 24 }, (_, hour) => ({
      hour,
      x: xForClockHour(hour),
      isCurrent: hour === nowHour,
    }));

    return {
      chartInnerWidth: CHART_INNER_WIDTH,
      chartHeight: CHART_HEIGHT,
      chartPad: CHART_PAD,
      plotW,
      plotH,
      maxKwh,
      hours,
      actual,
      predicted,
      predictionUnavailable,
      currentHour: nowHour,
      currentHourX,
      hourLabels,
      tariffRects,
      yTicks,
      realLinePath,
      predLinePath,
      realAreaPath,
      realPoints,
      baselineY,
    };
  }

  /** Eje Y: tope redondeado “amable” (1, 2, 5, 10 × potencia de 10) con margen visual. */
  private niceCeilKwh(peak: number): number {
    if (!Number.isFinite(peak) || peak <= 0) {
      return this.chartEmptyAxisMaxKwh();
    }
    const x = peak;
    const exp = Math.floor(Math.log10(x));
    const pow = Math.pow(10, exp);
    const f = x / pow;
    let nf: number;
    if (f <= 1) nf = 1;
    else if (f <= 2) nf = 2;
    else if (f <= 5) nf = 5;
    else nf = 10;
    return nf * pow;
  }

  /** Cuando no hay consumo, escala pequeña fija para que el gráfico no ocupe 0–1 kWh artificialmente. */
  private chartEmptyAxisMaxKwh(): number {
    return 0.1;
  }

  private formatYTickLabel(value: number, maxKwh: number): string {
    if (value <= 0 || Math.abs(value) < 1e-9) {
      return '0';
    }
    if (maxKwh < 0.15) {
      return value.toFixed(2);
    }
    if (maxKwh < 1.5) {
      return value.toFixed(1);
    }
    if (maxKwh < 20) {
      return String(Math.round(value * 10) / 10);
    }
    return String(Math.round(value));
  }
}
