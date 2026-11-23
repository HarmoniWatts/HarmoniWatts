import { Component, computed, DestroyRef, effect, inject, input, signal, untracked } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Observable, of } from 'rxjs';
import { catchError, switchMap } from 'rxjs/operators';
import { InfoTipComponent, type InfoTipTermino } from '../../../shared/components/info-tip';
import type { TarifaUbicacionResponse, UbicacionTarifaria } from '../../tarifas/tarifas.models';
import { TarifasService } from '../../tarifas/tarifas.service';
import type { DashboardPredictionResponse } from '../dashboard.models';
import { DashboardService } from '../dashboard.service';
import {
  diasDePrediccion,
  FRANJAS,
  horasDePrediccion,
  niceMax,
  resumen,
  tiposPorHora,
  type DiaPred,
  type Franja,
  type HoraPred,
} from './prediccion.util';

type Vista = 'dia' | 'hora' | 'franja';

const G = { w: 760, h: 240, left: 46, right: 10, top: 14, bottom: 30 } as const;
const PLOT_W = G.w - G.left - G.right;
const PLOT_H = G.h - G.top - G.bottom;
const BASE_Y = G.top + PLOT_H;

const FRANJA_LABEL: Record<Franja, string> = { VALLE: 'Valle', MEDIA: 'Media', PUNTA: 'Punta' };
const FRANJA_COLOR: Record<Franja, string> = { VALLE: '#1d8f52', MEDIA: '#d97706', PUNTA: '#c53030' };

const TIP_CONFIANZA: InfoTipTermino = {
  titulo: 'Confianza de la predicción',
  texto:
    'Cada día el modelo predice los días siguientes sin conocerlos. Comparamos esa predicción con tu consumo real de los últimos días: si el total diario se desvió en promedio 15 % o menos, la confianza es alta; hasta 30 %, media; más de 30 %, baja.',
};

/**
 * HAR-25: predicción del modelo vs consumo real de los últimos días, próximos días con su rango,
 * confianza de la predicción y vista por día, por hora o por franja tarifaria.
 */
@Component({
  selector: 'app-prediccion-card',
  standalone: true,
  imports: [InfoTipComponent],
  templateUrl: './prediccion-card.component.html',
  styleUrl: './prediccion-card.component.css',
})
export class PrediccionCardComponent {
  readonly noContrato = input<string | null>(null);
  readonly codComercializadora = input<string | null>(null);
  readonly ubicacion = input<UbicacionTarifaria | null>(null);

  private readonly api = inject(DashboardService);
  private readonly tarifasApi = inject(TarifasService);
  private readonly destroyRef = inject(DestroyRef);

  readonly g = G;
  readonly tipConfianza = TIP_CONFIANZA;
  readonly franjas = FRANJAS;
  readonly franjaLabel = FRANJA_LABEL;
  readonly franjaColor = FRANJA_COLOR;

  readonly vista = signal<Vista>('dia');
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly data = signal<DashboardPredictionResponse | null>(null);
  readonly tarifa = signal<TarifaUbicacionResponse | null>(null);
  readonly hover = signal<number | null>(null);

  readonly horas = computed(() => horasDePrediccion(this.data()));
  readonly tipos = computed(() => (this.tarifa() ? tiposPorHora(this.tarifa()!.precios) : null));
  readonly dias = computed(() =>
    diasDePrediccion(this.horas(), this.tipos(), this.data()?.confidence?.dailyErrorPct ?? null),
  );
  readonly totales = computed(() => resumen(this.dias()));

  readonly confianza = computed(() => {
    const c = this.data()?.confidence;
    if (!c) return null;
    const nivel = c.level === 'HIGH' ? 'Alta' : c.level === 'MEDIUM' ? 'Media' : 'Baja';
    return {
      nivel,
      clase: c.level === 'HIGH' ? 'pc-conf-alta' : c.level === 'MEDIUM' ? 'pc-conf-media' : 'pc-conf-baja',
      detalle:
        c.dailyErrorPct != null
          ? `Error diario promedio ${fmt(c.dailyErrorPct, 1)} % en los últimos ${c.daysEvaluated} días`
          : 'Aún no hay días suficientes para medir la precisión',
    };
  });

  /** Periodo de la tarifa usada para las franjas («octubre de 2026»). */
  readonly periodoTarifa = computed(() => {
    const p = this.tarifa()?.periodo;
    return p ? new Date(p.anio, p.mes - 1, 1).toLocaleDateString('es-CO', { month: 'long', year: 'numeric' }) : null;
  });

  // ---------------------------------------------------------------- gráfico por día / franja
  readonly vmDias = computed(() => {
    const dias = this.dias();
    if (!dias.length) return null;
    const max = niceMax(Math.max(...dias.map((d) => Math.max(d.sup ?? d.pred, d.real ?? 0, d.pred)), 0.01) * 1.05);
    const y = (v: number) => G.top + (1 - v / max) * PLOT_H;
    const slot = PLOT_W / dias.length;
    const iFuturo = dias.findIndex((d) => d.futuro);
    const col = dias.map((d, i) => {
      const x0 = G.left + i * slot;
      const w = slot * 0.32;
      const conReal = d.real != null;
      const xReal = x0 + slot / 2 - w - 1;
      const xPred = conReal ? x0 + slot / 2 + 1 : x0 + slot / 2 - w / 2;
      let acc = 0;
      const pila = FRANJAS.map((f) => {
        const v = d.franjas[f];
        const y1 = y(acc + v);
        const y0 = y(acc);
        acc += v;
        return { f, y: y1, h: Math.max(0, y0 - y1) };
      });
      return {
        d,
        x0,
        slot,
        cx: x0 + slot / 2,
        real: conReal ? { x: xReal, y: y(d.real!), w, h: BASE_Y - y(d.real!) } : null,
        pred: { x: xPred, y: y(d.pred), w, h: BASE_Y - y(d.pred) },
        rango: d.inf != null && d.sup != null ? { y1: y(d.sup), y2: y(d.inf) } : null,
        pila,
        pilaX: x0 + slot * 0.26,
        pilaW: slot * 0.48,
        realMarca: conReal ? y(d.real!) : null,
        label: etiquetaDia(d.dia),
      };
    });
    return {
      col,
      yTicks: ticks(max, y),
      separadorX: iFuturo > 0 ? G.left + iFuturo * slot : null,
    };
  });

  // ---------------------------------------------------------------- gráfico por hora
  readonly vmHoras = computed(() => {
    const hs = this.horas();
    if (!hs.length) return null;
    const max = niceMax(Math.max(...hs.map((h) => Math.max(h.sup ?? h.pred, h.real ?? 0)), 0.01) * 1.05);
    const n = hs.length;
    const x = (i: number) => G.left + (n === 1 ? 0 : (i / (n - 1)) * PLOT_W);
    const y = (v: number) => G.top + (1 - v / max) * PLOT_H;
    const linea = (pts: [number, number][]) => pts.map(([px, py], i) => `${i ? 'L' : 'M'}${px.toFixed(1)},${py.toFixed(1)}`).join(' ');
    const reales = hs.map((h, i) => [h, i] as const).filter(([h]) => h.real != null);
    const futuros = hs.map((h, i) => [h, i] as const).filter(([h]) => h.futuro);
    const banda = futuros.length
      ? linea(futuros.map(([h, i]) => [x(i), y(h.sup!)])) +
        ' ' +
        futuros
          .slice()
          .reverse()
          .map(([h, i]) => `L${x(i).toFixed(1)},${y(h.inf!).toFixed(1)}`)
          .join(' ') +
        ' Z'
      : '';
    const iAhora = hs.findIndex((h) => h.futuro);
    const xLabels = hs
      .map((h, i) => ({ h, i }))
      .filter(({ h }) => h.hora === 0)
      .map(({ h, i }) => ({ x: x(i), label: etiquetaDia(h.dia) }));
    return {
      real: linea(reales.map(([h, i]) => [x(i), y(h.real!)])),
      pred: linea(hs.map((h, i) => [x(i), y(h.pred)])),
      banda,
      ahoraX: iAhora > 0 ? x(iAhora) : null,
      yTicks: ticks(max, y),
      xLabels,
      slotW: PLOT_W / Math.max(1, n - 1),
      x,
      y,
    };
  });

  // ---------------------------------------------------------------- tooltip
  readonly tooltip = computed(() => {
    const i = this.hover();
    if (i == null) return null;
    if (this.vista() === 'hora') {
      const h = this.horas()[i];
      const vm = this.vmHoras();
      if (!h || !vm) return null;
      return {
        xPct: (vm.x(i) / G.w) * 100,
        titulo: `${etiquetaDia(h.dia, true)} · ${String(h.hora).padStart(2, '0')}:00`,
        filas: filasHora(h),
      };
    }
    const vm = this.vmDias();
    const c = vm?.col[i];
    if (!c) return null;
    return {
      xPct: (c.cx / G.w) * 100,
      titulo: etiquetaDia(c.d.dia, true),
      filas: this.vista() === 'franja' ? filasFranja(c.d, this.tipos() != null) : filasDia(c.d),
    };
  });

  constructor() {
    effect(() => {
      const no = this.noContrato();
      const cod = this.codComercializadora();
      untracked(() => this.cargar(no, cod));
    });
    effect(() => {
      const u = this.ubicacion();
      untracked(() => this.cargarTarifa(u));
    });
  }

  setVista(v: Vista): void {
    this.vista.set(v);
    this.hover.set(null);
  }

  recargar(): void {
    this.cargar(this.noContrato(), this.codComercializadora());
  }

  private cargar(no: string | null, cod: string | null): void {
    this.data.set(null);
    this.error.set(null);
    this.hover.set(null);
    if (!no || !cod) return;
    this.loading.set(true);
    this.api
      .getPrediction({ noContrato: no, codComercializadora: cod })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (r) => {
          this.data.set(r);
          this.loading.set(false);
        },
        error: () => {
          this.error.set('El servicio de predicción no está disponible en este momento.');
          this.loading.set(false);
        },
      });
  }

  /** Tarifa vigente; si el mes no está publicado, la última publicada (solo para las franjas). */
  private cargarTarifa(u: UbicacionTarifaria | null): void {
    this.tarifa.set(null);
    if (!u) return;
    this.tarifasApi
      .getTarifa(u)
      .pipe(
        catchError(() => this.ultimaTarifa(u)),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((t) => this.tarifa.set(t));
  }

  private ultimaTarifa(u: UbicacionTarifaria, anio = new Date().getFullYear(), intentos = 2): Observable<TarifaUbicacionResponse | null> {
    if (intentos <= 0) return of(null);
    return this.tarifasApi.getCalendario(u, anio).pipe(
      switchMap((cal) => {
        const mes = [...cal.meses].reverse().find((m) => m.publicado);
        if (!mes) return this.ultimaTarifa(u, anio - 1, intentos - 1);
        return this.tarifasApi.getTarifa(u, `${anio}-${String(mes.mes).padStart(2, '0')}-01`);
      }),
      catchError(() => of(null)),
    );
  }

  fmt = fmt;
}

function ticks(max: number, y: (v: number) => number): { y: number; label: string }[] {
  return [0, 0.25, 0.5, 0.75, 1].map((f) => ({ y: y(max * f), label: fmt(max * f, max < 1 ? 2 : 1) }));
}

function etiquetaDia(dia: string, largo = false): string {
  const [a, m, d] = dia.split('-').map(Number);
  const f = new Date(a, m - 1, d);
  return f.toLocaleDateString('es-CO', largo ? { weekday: 'long', day: 'numeric', month: 'short' } : { weekday: 'short', day: 'numeric' });
}

function filasHora(h: HoraPred): { k: string; v: string; clase?: string }[] {
  const out: { k: string; v: string; clase?: string }[] = [];
  if (h.real != null) out.push({ k: 'Consumo real', v: `${fmt(h.real, 3)} kWh`, clase: 'pc-k-real' });
  out.push({ k: h.futuro ? 'Predicción' : 'Predicho', v: `${fmt(h.pred, 3)} kWh`, clase: 'pc-k-pred' });
  if (h.inf != null && h.sup != null) out.push({ k: 'Rango probable', v: `${fmt(h.inf, 3)} – ${fmt(h.sup, 3)} kWh` });
  return out;
}

function filasDia(d: DiaPred): { k: string; v: string; clase?: string }[] {
  const out: { k: string; v: string; clase?: string }[] = [];
  if (d.real != null) {
    const parcial = d.horasReales < 24 ? ` (hasta las ${String(d.horasReales).padStart(2, '0')}:00)` : '';
    out.push({ k: `Consumo real${parcial}`, v: `${fmt(d.real, 2)} kWh`, clase: 'pc-k-real' });
  }
  out.push({ k: d.futuro ? 'Predicción del día' : 'Predicho', v: `${fmt(d.pred, 2)} kWh`, clase: 'pc-k-pred' });
  if (d.real != null && d.horasReales === 24 && d.real > 0) {
    out.push({ k: 'Diferencia', v: `${fmt(((d.pred - d.real) / d.real) * 100, 0)} %` });
  }
  if (d.inf != null && d.sup != null) out.push({ k: 'Rango probable', v: `${fmt(d.inf, 1)} – ${fmt(d.sup, 1)} kWh` });
  return out;
}

function filasFranja(d: DiaPred, hayTarifa: boolean): { k: string; v: string; clase?: string }[] {
  const out: { k: string; v: string; clase?: string }[] = FRANJAS.map((f) => ({
    k: `${FRANJA_LABEL[f]}${hayTarifa ? '' : ' (sin tarifa)'}`,
    v: `${fmt(d.franjas[f], 2)} kWh`,
    clase: `pc-k-${f.toLowerCase()}`,
  }));
  out.push({ k: 'Total predicho', v: `${fmt(d.pred, 2)} kWh` });
  if (d.real != null && d.horasReales === 24) out.push({ k: 'Consumo real', v: `${fmt(d.real, 2)} kWh`, clase: 'pc-k-real' });
  return out;
}

function fmt(v: number | null | undefined, dec = 1): string {
  if (v == null || Number.isNaN(v)) return '—';
  return v.toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: dec });
}
