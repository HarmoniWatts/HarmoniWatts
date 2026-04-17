import { CommonModule } from '@angular/common';
import { Component, DestroyRef, inject, OnInit, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { forkJoin, of } from 'rxjs';
import { catchError, finalize } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { DashboardService } from './dashboard.service';
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
  currentHour: number;
  currentHourX: number;
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
  imports: [CommonModule],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css',
})
export class DashboardComponent implements OnInit {
  private readonly dashboardApi = inject(DashboardService);
  private readonly destroyRef = inject(DestroyRef);

  readonly loading = signal(true);
  readonly selectedDate = signal(this.todayYmd());

  summary: DashboardSummaryResponse | null = null;
  chart: DashboardConsumptionChartResponse | null = null;
  recommendations: DashboardRecommendationsResponse | null = null;
  appliances: DashboardAppliancesTopResponse | null = null;

  chartVm: ChartViewModel | null = null;

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
      return { bg: '#22c55e', fg: 'var(--dash-franja-fg-dark)' };
    }
    if (t === 'PUNTA') {
      return { bg: '#b91c1c', fg: '#ffffff' };
    }
    return { bg: '#eab308', fg: 'var(--dash-franja-fg-dark)' };
  }

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
    const activeIdx = this.activeBandIndex(bands, chart.currentHourLocal);
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

  private loadAll(): void {
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
          this.summary = summary;
          this.chart = chart;
          this.recommendations = recommendations;
          this.appliances = appliances;
          this.chartVm = chart ? this.buildChartView(chart) : null;
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

    const maxFromData = Math.max(1, ...actual, ...(predicted ?? []));
    const maxKwh = Math.max(chart.maxKwhScale ?? 0, maxFromData, 1);

    const plotW = CHART_INNER_WIDTH - CHART_PAD.left - CHART_PAD.right;
    const plotH = CHART_HEIGHT - CHART_PAD.top - CHART_PAD.bottom;

    const xForClockHour = (hod: number) =>
      CHART_PAD.left + (Math.min(23, Math.max(0, hod)) / 23) * plotW;
    const xDayFrac = (t: number) => CHART_PAD.left + (t / 24) * plotW;
    const yForKwh = (val: number) => CHART_PAD.top + (1 - val / maxKwh) * plotH;
    const baselineY = CHART_HEIGHT - CHART_PAD.bottom;

    const n = Math.max(actual.length, predicted?.length ?? 0, hours.length, 1);
    const realPoints: { x: number; y: number; isCurrent: boolean }[] = [];
    for (let idx = 0; idx < n; idx++) {
      const hodRaw = hours[idx];
      const hod = typeof hodRaw === 'number' ? hodRaw : idx;
      const v = actual[Math.min(idx, actual.length - 1)] ?? 0;
      realPoints.push({
        x: xForClockHour(hod),
        y: yForKwh(v),
        isCurrent: hod === chart.currentHourLocal,
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
      const label = value < 0.05 ? '0' : value >= 10 ? String(Math.round(value)) : value.toFixed(1);
      yTicks.push({ value, y, label });
    }

    const ch = Math.min(23, Math.max(0, chart.currentHourLocal));
    const currentHourX = xForClockHour(ch);
    const hourLabels = Array.from({ length: 24 }, (_, hour) => ({
      hour,
      x: xForClockHour(hour),
      isCurrent: hour === ch,
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
      currentHour: chart.currentHourLocal,
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
}
