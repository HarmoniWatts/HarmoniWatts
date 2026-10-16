import { CommonModule } from '@angular/common';
import { Component, computed, DestroyRef, effect, inject, signal, untracked } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { HttpErrorResponse } from '@angular/common/http';
import { of } from 'rxjs';
import { catchError, finalize } from 'rxjs/operators';
import { ViviendaContextService } from '../vivienda/vivienda-context.service';
import { ViviendaSelectorComponent } from '../vivienda/vivienda-selector.component';
import { InfoTipComponent, type InfoTipTermino } from '../../shared/components/info-tip';
import { GLOSARIO } from './tarifas-glosario';
import type { TariffType } from '../dashboard/dashboard.models';
import {
  tariffTypeLabel,
  toCurrentTariffSlot,
  toDashboardTariffType,
  toTariffBands,
} from './tariff-dashboard.adapter';
import type {
  CalendarioTarifasResponse,
  MesCalendario,
  TarifaUbicacionResponse,
  UbicacionTarifaria,
} from './tarifas.models';
import { TarifasService } from './tarifas.service';

const MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
const MESES_LARGO = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
];

const CHART = { w: 1000, h: 280, left: 64, right: 12, top: 12, bottom: 34 } as const;


export interface PriceChartVm {
  w: number;
  h: number;
  plotTop: number;
  plotBottom: number;
  left: number;
  bars: { x: number; y: number; width: number; height: number; color: string; title: string; isNow: boolean }[];
  yTicks: { y: number; label: string }[];
  xLabels: { x: number; label: string }[];
  nowX: number | null;
}

@Component({
  selector: 'app-tarifas-page',
  standalone: true,
  imports: [CommonModule, ViviendaSelectorComponent, InfoTipComponent],
  templateUrl: './tarifas-page.component.html',
  styleUrl: './tarifas-page.component.css',
})
export class TarifasPageComponent {
  private readonly api = inject(TarifasService);
  private readonly destroyRef = inject(DestroyRef);
  protected readonly ctx = inject(ViviendaContextService);

  readonly meses = MESES;
  /** Textos de los botones informativos. */
  readonly g = GLOSARIO;
  readonly fecha = signal(todayYmd());
  readonly anio = signal(new Date().getFullYear());

  readonly tarifa = signal<TarifaUbicacionResponse | null>(null);
  readonly calendario = signal<CalendarioTarifasResponse | null>(null);
  readonly loadingTarifa = signal(false);
  readonly loadingCalendario = signal(false);
  readonly error = signal<string | null>(null);
  /** Aviso cuando se muestra otro mes porque el consultado no está publicado. */
  readonly aviso = signal<string | null>(null);

  /** Hora de reloj para "tarifa actual": la actual si se consulta hoy; si no, mediodía. */
  readonly horaReferencia = computed(() => (this.fecha() === todayYmd() ? new Date().getHours() : null));

  readonly actual = computed(() => {
    const t = this.tarifa();
    if (!t) return null;
    return toCurrentTariffSlot(t.precios, this.horaReferencia() ?? 12);
  });

  readonly bandas = computed(() => toTariffBands(this.tarifa()?.precios ?? []));

  readonly chartVm = computed(() => {
    const t = this.tarifa();
    return t ? buildPriceChart(t, this.horaReferencia()) : null;
  });

  readonly resumenPrecios = computed(() => {
    const valores = (this.tarifa()?.precios ?? []).map((p) => p.precio).filter((v): v is number => v != null);
    if (!valores.length) return null;
    const min = Math.min(...valores);
    const max = Math.max(...valores);
    return { min, max, diferencia: max - min, pct: min > 0 ? ((max - min) / min) * 100 : 0 };
  });

  constructor() {
    // Recarga al cambiar de vivienda (o cuando terminan de cargar las viviendas)
    effect(() => {
      const u = this.ctx.ubicacion();
      untracked(() => {
        this.tarifa.set(null);
        this.calendario.set(null);
        this.aviso.set(null);
        this.error.set(null);
        if (u) {
          this.cargarCalendario(u);
          this.cargarTarifa(u, true);
        }
      });
    });
  }

  onFechaChange(value: string): void {
    if (!value) return;
    this.fecha.set(value);
    this.aviso.set(null);
    const u = this.ctx.ubicacion();
    if (!u) return;
    const anio = Number(value.slice(0, 4));
    if (anio !== this.anio()) {
      this.anio.set(anio);
      this.cargarCalendario(u);
    }
    this.cargarTarifa(u, false);
  }

  cambiarAnio(delta: number): void {
    this.anio.update((a) => a + delta);
    const u = this.ctx.ubicacion();
    if (u) this.cargarCalendario(u);
  }

  verMes(m: MesCalendario): void {
    if (!m.publicado) return;
    const hoy = todayYmd();
    const prefijo = `${this.anio()}-${pad(m.mes)}`;
    this.onFechaChange(hoy.startsWith(prefijo) ? hoy : `${prefijo}-01`);
  }

  esMesSeleccionado(m: MesCalendario): boolean {
    return this.fecha().startsWith(`${this.anio()}-${pad(m.mes)}`);
  }

  esMesActual(m: MesCalendario): boolean {
    return todayYmd().startsWith(`${this.anio()}-${pad(m.mes)}`);
  }

  recargar(): void {
    const u = this.ctx.ubicacion();
    if (u) {
      this.cargarCalendario(u);
      this.cargarTarifa(u, false);
    }
  }

  tipoLabel(type: TariffType): string {
    return tariffTypeLabel(type);
  }

  tipoClase(type: TariffType | null | undefined): string {
    return `tf-tipo-${String(type ?? 'MEDIA').toLowerCase()}`;
  }

  tipoDeHora(tipo: TarifaUbicacionResponse['precios'][number]['tipo_hora']): TariffType {
    return toDashboardTariffType(tipo);
  }

  terminoComponente(cod: string): InfoTipTermino {
    return (GLOSARIO as Record<string, InfoTipTermino>)[cod] ?? { titulo: cod, texto: 'Componente del costo unitario publicado por la comercializadora.' };
  }

  componenteNombre(cod: string): string {
    return this.terminoComponente(cod).titulo.replace(/\s*\(.*\)$/, '');
  }

  nombreMes(mes: number): string {
    return MESES_LARGO[mes - 1] ?? String(mes);
  }

  formatCop(value: number | null | undefined, decimals = 2): string {
    if (value == null || Number.isNaN(value)) return '—';
    return new Intl.NumberFormat('es-CO', { minimumFractionDigits: decimals, maximumFractionDigits: decimals }).format(value);
  }

  hh(h: number): string {
    return `${pad(h)}:00`;
  }

  private cargarTarifa(u: UbicacionTarifaria, permitirRespaldo: boolean): void {
    this.loadingTarifa.set(true);
    this.error.set(null);
    this.api
      .getTarifa(u, this.fecha())
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        catchError((err: HttpErrorResponse) => {
          if (err.status === 404 && permitirRespaldo) {
            this.mostrarUltimoPublicado(u);
          } else if (err.status === 404) {
            this.error.set(`No hay tarifa publicada para ${this.describirFecha(this.fecha())}.`);
          } else {
            this.error.set('No se pudo consultar la tarifa. ¿Está levantado tariff-service (puerto 8006)?');
          }
          return of(null);
        }),
        finalize(() => this.loadingTarifa.set(false)),
      )
      .subscribe((t) => {
        if (t) this.tarifa.set(t);
      });
  }

  /** El mes consultado no está publicado: busca el último mes publicado (año actual o anterior). */
  private mostrarUltimoPublicado(u: UbicacionTarifaria): void {
    const anio = Number(this.fecha().slice(0, 4));
    const pendiente = this.describirFecha(this.fecha());
    const buscar = (y: number, intentos: number): void => {
      this.api
        .getCalendario(u, y)
        .pipe(takeUntilDestroyed(this.destroyRef), catchError(() => of(null)))
        .subscribe((cal) => {
          const ultimo = cal?.meses.filter((m) => m.publicado).pop();
          if (ultimo) {
            this.aviso.set(
              `La tarifa de ${pendiente} aún no está publicada; se muestra ${this.nombreMes(ultimo.mes)} ${y}.`,
            );
            if (y !== this.anio()) {
              this.anio.set(y);
              this.calendario.set(cal);
            }
            this.fecha.set(`${y}-${pad(ultimo.mes)}-01`);
            this.cargarTarifa(u, false);
          } else if (intentos > 0) {
            buscar(y - 1, intentos - 1);
          } else {
            this.error.set('Aún no hay tarifas publicadas para la ubicación de esta vivienda.');
          }
        });
    };
    buscar(anio, 1);
  }

  private cargarCalendario(u: UbicacionTarifaria): void {
    this.loadingCalendario.set(true);
    this.api
      .getCalendario(u, this.anio())
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        catchError(() => of(null)),
        finalize(() => this.loadingCalendario.set(false)),
      )
      .subscribe((cal) => this.calendario.set(cal));
  }

  private describirFecha(ymd: string): string {
    const [y, m] = ymd.split('-').map(Number);
    return `${this.nombreMes(m)} ${y}`;
  }
}

function buildPriceChart(t: TarifaUbicacionResponse, horaActual: number | null): PriceChartVm {
  const plotW = CHART.w - CHART.left - CHART.right;
  const plotTop = CHART.top;
  const plotBottom = CHART.h - CHART.bottom;
  const plotH = plotBottom - plotTop;

  const valores = t.precios.map((p) => p.precio).filter((v): v is number => v != null);
  const min = valores.length ? Math.min(...valores) : 0;
  const max = valores.length ? Math.max(...valores) : 1;
  // Las franjas difieren poco (≈2 %): el eje parte cerca del mínimo para que la diferencia se vea.
  const rango = Math.max(max - min, max * 0.01);
  const step = niceStep(rango / 2);
  const yMin = Math.max(0, Math.floor((min - rango * 0.6) / step) * step);
  const yMax = Math.ceil((max + rango * 0.15) / step) * step;
  const y = (v: number) => plotTop + (1 - (v - yMin) / (yMax - yMin)) * plotH;

  const slot = plotW / 24;
  const bars = t.precios.map((p) => {
    const clock = p.hora - 1;
    const precio = p.precio ?? yMin;
    const type = toDashboardTariffType(p.tipo_hora);
    return {
      x: CHART.left + clock * slot + slot * 0.12,
      y: y(precio),
      width: slot * 0.76,
      height: Math.max(0, plotBottom - y(precio)),
      color: barColor(type),
      title: `${pad(clock)}:00–${pad(clock + 1)}:00 · ${p.codigo_franja ?? '—'} · ${tariffTypeLabel(type)} · ${p.precio ?? '—'} COP/kWh`,
      isNow: horaActual === clock,
    };
  });

  const yTicks = [];
  for (let v = yMin; v <= yMax + step / 2; v += step) {
    yTicks.push({ y: y(v), label: new Intl.NumberFormat('es-CO').format(Math.round(v)) });
  }
  const xLabels = Array.from({ length: 24 }, (_, h) => ({ x: CHART.left + h * slot + slot / 2, label: pad(h) }));

  return {
    w: CHART.w,
    h: CHART.h,
    plotTop,
    plotBottom,
    left: CHART.left,
    bars,
    yTicks,
    xLabels,
    nowX: horaActual != null ? CHART.left + horaActual * slot + slot / 2 : null,
  };
}

function niceStep(raw: number): number {
  if (!Number.isFinite(raw) || raw <= 0) return 1;
  const pow = Math.pow(10, Math.floor(Math.log10(raw)));
  const f = raw / pow;
  return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10) * pow;
}

function barColor(type: TariffType): string {
  const t = String(type).toUpperCase();
  if (t === 'VALLE') return '#1d8f52';
  if (t === 'PUNTA') return '#c53030';
  return '#b45309';
}

function pad(n: number): string {
  return String(n).padStart(2, '0');
}

function todayYmd(): string {
  const d = new Date();
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}
