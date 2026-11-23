import { CommonModule } from '@angular/common';
import { Component, computed, DestroyRef, effect, inject, signal, untracked } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { forkJoin, Observable, of } from 'rxjs';
import { catchError, finalize, switchMap } from 'rxjs/operators';
import { InfoTipComponent, type InfoTipTermino } from '../../../shared/components/info-tip';
import type { TarifaUbicacionResponse, TipoHora, UbicacionTarifaria } from '../../tarifas/tarifas.models';
import { TarifasService } from '../../tarifas/tarifas.service';
import { ViviendaContextService } from '../../vivienda/vivienda-context.service';
import { ViviendaSelectorComponent } from '../../vivienda/vivienda-selector.component';
import { HorarioEditorComponent } from '../horario-editor/horario-editor.component';
import { PotenciaInputComponent } from '../potencia-input/potencia-input.component';
import type {
  ElectrodomesticoDto,
  ElectrodomesticoUpdatePayload,
  EstimacionElectrodomestico,
  EstimacionViviendaResponse,
  HorarioUso,
} from '../electrodomesticos.service';
import { ElectrodomesticosService } from '../electrodomesticos.service';
import {
  colorFor,
  costoMensual,
  DIAS_CORTOS,
  DIAS_LARGOS,
  DIAS_POR_MES,
  donutSlices,
  duracionHoras,
  fraccionEnTipo,
  FUENTE_LABEL,
  niceMax,
  preciosPorHora,
  sum,
  tendenciaDiaria,
  tiposPorHora,
} from './estimacion.util';

/** Fila del ranking con color y costo ya resueltos. */
export interface RankingRow extends EstimacionElectrodomestico {
  color: string;
  costoMes: number | null;
  /** 0–1 del consumo que cae en hora pico (solo si hay tarifa con franjas). */
  fraccionPico: number | null;
}

interface Borrador {
  potenciaW: number | null;
  usarAjuste: boolean;
  consumoAjustadoKwhMes: number | null;
  esDesplazable: boolean;
  activo: boolean;
  horarios: HorarioUso[];
}

const CH = { w: 760, h: 240, left: 46, right: 8, top: 10, bottom: 26 } as const;
const TR = { w: 760, h: 180, left: 46, right: 8, top: 10, bottom: 26 } as const;

const TIPS: Record<string, InfoTipTermino> = {
  ranking: {
    titulo: 'Ranking de consumo',
    texto:
      'Ordena tus electrodomésticos activos por el consumo mensual estimado. Haz clic en uno para ver su tendencia y ajustar sus datos.',
  },
  perfil: {
    titulo: 'Consumo por hora',
    texto:
      'Reparte el consumo estimado de cada electrodoméstico en las horas en que dijiste usarlo. Los que están siempre encendidos reparten su promedio diario en las 24 h. El fondo muestra las franjas valle / media / pico de tu tarifa.',
  },
  optimizable: {
    titulo: 'Optimizable',
    texto:
      'Un electrodoméstico desplazable (lavadora, lavavajillas, carga del EV…) puede moverse a horas valle para pagar menos. Los no desplazables (nevera, TV) se usan cuando se necesitan.',
  },
  estimacion: {
    titulo: 'Cómo se estima',
    texto:
      'Potencia (W) × horas de uso de tu horario ÷ 1000. Si está siempre encendido se cuentan las 24 h. Si tu etiqueta dice kWh/mes, la calculadora lo convierte a W según tu horario. Si conoces el valor real (medidor, factura) usa «Ajustar consumo»: prevalece sobre el cálculo.',
  },
};

@Component({
  selector: 'app-electrodomesticos-gestion',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, ViviendaSelectorComponent, InfoTipComponent, HorarioEditorComponent, PotenciaInputComponent],
  templateUrl: './electrodomesticos-gestion.component.html',
  styleUrl: './electrodomesticos-gestion.component.css',
})
export class ElectrodomesticosGestionComponent {
  private readonly api = inject(ElectrodomesticosService);
  private readonly tarifasApi = inject(TarifasService);
  private readonly destroyRef = inject(DestroyRef);
  protected readonly ctx = inject(ViviendaContextService);

  readonly tips = TIPS;
  readonly diasCortos = DIAS_CORTOS;
  readonly diasLargos = DIAS_LARGOS;
  readonly fuenteLabel = FUENTE_LABEL;
  readonly ch = CH;
  readonly tr = TR;

  readonly loading = signal(false);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);
  readonly okMsg = signal<string | null>(null);

  readonly estimacion = signal<EstimacionViviendaResponse | null>(null);
  readonly items = signal<ElectrodomesticoDto[]>([]);
  readonly tarifa = signal<TarifaUbicacionResponse | null>(null);

  readonly selectedId = signal<number | null>(null);
  readonly hoverId = signal<number | null>(null);
  /** Día mostrado en el gráfico por hora (0 = lunes). */
  readonly diaPerfil = signal((new Date().getDay() + 6) % 7);
  readonly borrador = signal<Borrador | null>(null);

  // ---------------------------------------------------------------- tarifa
  private readonly precioHora = computed(() => {
    const t = this.tarifa();
    return t ? preciosPorHora(t.precios, t.monomia?.valor ?? null) : null;
  });
  readonly tipoHora = computed<(TipoHora | null)[]>(() => tiposPorHora(this.tarifa()?.precios ?? []));
  private readonly hayFranjas = computed(() => this.tipoHora().some((t) => t != null));

  // ---------------------------------------------------------------- ranking
  readonly rows = computed<RankingRow[]>(() => {
    const est = this.estimacion();
    if (!est) return [];
    const precio = this.precioHora();
    let i = 0;
    return est.electrodomesticos.map((e) => ({
      ...e,
      color: e.activo ? colorFor(i++) : 'var(--color-text-subtle)',
      costoMes: precio ? costoMensual(e.perfilSemanal, precio) : null,
      fraccionPico: this.hayFranjas() ? fraccionEnTipo(e.perfilSemanal, this.tipoHora(), 'PICO') : null,
    }));
  });
  readonly activos = computed(() => this.rows().filter((r) => r.activo));
  readonly maxKwhMes = computed(() => Math.max(0, ...this.activos().map((r) => r.kwhMes)));
  readonly selected = computed(() => this.rows().find((r) => r.id === this.selectedId()) ?? null);
  readonly selectedDto = computed(() => this.items().find((i) => i.id === this.selectedId()) ?? null);

  // ---------------------------------------------------------------- KPIs
  readonly kpis = computed(() => {
    const est = this.estimacion();
    const act = this.activos();
    if (!est) return null;
    const costos = act.map((r) => r.costoMes);
    const costoTotal = costos.every((c) => c != null) && act.length ? sum(costos as number[]) : null;
    const optim = act.filter((r) => r.optimizable);
    const kwhOptim = sum(optim.map((r) => r.kwhMes));
    return {
      totalKwhMes: est.totalKwhMes,
      totalKwhDia: est.totalKwhDia,
      costoTotal,
      top: act[0] ?? null,
      optimizables: optim.length,
      noOptimizables: act.length - optim.length,
      pctOptimizable: est.totalKwhMes > 0 ? (kwhOptim * 100) / est.totalKwhMes : 0,
    };
  });

  // ---------------------------------------------------------------- dona
  readonly donut = computed(() =>
    donutSlices(
      this.activos().map((r) => ({ id: r.id, label: r.nombre, value: r.kwhMes, color: r.color })),
      100,
      62,
    ),
  );

  // ---------------------------------------------------------------- por hora
  readonly perfilVm = computed(() => {
    const d = this.diaPerfil();
    const act = this.activos();
    const totales = Array.from({ length: 24 }, (_, h) => sum(act.map((r) => r.perfilSemanal[d]?.[h] ?? 0)));
    const max = niceMax(Math.max(...totales, 0.001));
    const plotW = CH.w - CH.left - CH.right;
    const plotH = CH.h - CH.top - CH.bottom;
    const slot = plotW / 24;
    const bw = slot * 0.7;
    const y = (v: number) => CH.top + plotH - (v / max) * plotH;
    const sel = this.selectedId();
    const bars: { x: number; y: number; w: number; h: number; color: string; dim: boolean; title: string }[] = [];
    for (let h = 0; h < 24; h++) {
      let acc = 0;
      for (const r of act) {
        const v = r.perfilSemanal[d]?.[h] ?? 0;
        if (v <= 0) continue;
        const y0 = y(acc);
        acc += v;
        const y1 = y(acc);
        bars.push({
          x: CH.left + h * slot + (slot - bw) / 2,
          y: y1,
          w: bw,
          h: Math.max(0.5, y0 - y1),
          color: r.color,
          dim: sel != null && sel !== r.id,
          title: `${r.nombre} · ${hh(h)}–${hh(h + 1)}: ${fmt(v, 3)} kWh`,
        });
      }
    }
    const bandas = this.tipoHora().map((t, h) => ({ x: CH.left + h * slot, w: slot, tipo: t }));
    const yTicks = [0, 0.25, 0.5, 0.75, 1].map((f) => ({ y: y(max * f), label: fmt(max * f, max < 1 ? 2 : 1) }));
    const xLabels = [0, 3, 6, 9, 12, 15, 18, 21].map((h) => ({ x: CH.left + h * slot + slot / 2, label: hh(h) }));
    return { bars, bandas, yTicks, xLabels, totalDia: sum(totales), plotBottom: CH.top + plotH };
  });

  // ---------------------------------------------------------------- tendencia
  readonly tendenciaVm = computed(() => {
    const r = this.selected();
    if (!r) return null;
    const serie = tendenciaDiaria(r.perfilSemanal, 30);
    const max = niceMax(Math.max(...serie.map((s) => s.kwh), 0.001));
    const plotW = TR.w - TR.left - TR.right;
    const plotH = TR.h - TR.top - TR.bottom;
    const slot = plotW / serie.length;
    const y = (v: number) => TR.top + plotH - (v / max) * plotH;
    const bars = serie.map((s, i) => ({
      x: TR.left + i * slot + slot * 0.15,
      y: y(s.kwh),
      w: slot * 0.7,
      h: Math.max(0, TR.top + plotH - y(s.kwh)),
      finde: s.fecha.getDay() === 0 || s.fecha.getDay() === 6,
      title: `${s.fecha.toLocaleDateString('es-CO', { weekday: 'short', day: 'numeric', month: 'short' })}: ${fmt(s.kwh, 3)} kWh`,
    }));
    const promedio = sum(serie.map((s) => s.kwh)) / serie.length;
    const xLabels = serie
      .map((s, i) => ({ i, s }))
      .filter(({ i }) => i % 5 === 0 || i === serie.length - 1)
      .map(({ i, s }) => ({
        x: TR.left + i * slot + slot / 2,
        label: s.fecha.toLocaleDateString('es-CO', { day: 'numeric', month: 'short' }),
      }));
    const yTicks = [0, 0.5, 1].map((f) => ({ y: y(max * f), label: fmt(max * f, max < 1 ? 2 : 1) }));
    return {
      bars,
      xLabels,
      yTicks,
      promedioY: y(promedio),
      promedio,
      total30: sum(serie.map((s) => s.kwh)),
      porDia: DIAS_CORTOS.map((d, i) => ({ dia: d, kwh: sum(r.perfilSemanal[i] ?? []) })),
      plotBottom: TR.top + plotH,
    };
  });

  // ---------------------------------------------------------------- editor
  /** Vista previa del cálculo con el borrador (misma regla que el backend). */
  readonly preview = computed(() => {
    const b = this.borrador();
    if (!b) return null;
    const horas = this.horasSemanaBorrador();
    if (b.usarAjuste && b.consumoAjustadoKwhMes != null && b.consumoAjustadoKwhMes >= 0) {
      return { kwhMes: b.consumoAjustadoKwhMes, horas, fuente: FUENTE_LABEL.AJUSTE_USUARIO };
    }
    const w = b.potenciaW && b.potenciaW > 0 ? b.potenciaW : 0;
    return { kwhMes: ((horas * w) / 1000) * (DIAS_POR_MES / 7), horas, fuente: FUENTE_LABEL.HORARIO_POTENCIA };
  });

  /** Horas de uso por semana del borrador (168 = siempre encendido). */
  readonly horasSemanaBorrador = computed(() => {
    const hs = this.borrador()?.horarios ?? [];
    return hs.length ? sum(hs.map(duracionHoras)) : 168;
  });

  constructor() {
    effect(() => {
      const v = this.ctx.selected();
      untracked(() => {
        this.estimacion.set(null);
        this.items.set([]);
        this.selectedId.set(null);
        this.borrador.set(null);
        if (v) this.cargar(v.id);
      });
    });
    effect(() => {
      const u = this.ctx.ubicacion();
      untracked(() => {
        this.tarifa.set(null);
        if (!u) return;
        this.tarifasApi
          .getTarifa(u)
          .pipe(
            // Mes actual sin publicar → último mes publicado (como en «Tarifas»)
            catchError(() => this.ultimaTarifaPublicada(u)),
            takeUntilDestroyed(this.destroyRef),
          )
          .subscribe((t) => this.tarifa.set(t));
      });
    });
  }

  private ultimaTarifaPublicada(u: UbicacionTarifaria, anio = new Date().getFullYear(), intentos = 2): Observable<TarifaUbicacionResponse | null> {
    if (intentos <= 0) return of(null);
    return this.tarifasApi.getCalendario(u, anio).pipe(
      switchMap((cal) => {
        const mes = [...cal.meses].reverse().find((m) => m.publicado);
        if (!mes) return this.ultimaTarifaPublicada(u, anio - 1, intentos - 1);
        return this.tarifasApi.getTarifa(u, `${anio}-${String(mes.mes).padStart(2, '0')}-01`);
      }),
      catchError(() => of(null)),
    );
  }

  /** «nov 2026» del periodo tarifario usado para el costo. */
  periodoTarifa(): string | null {
    const p = this.tarifa()?.periodo;
    if (!p) return null;
    return new Date(p.anio, p.mes - 1, 1).toLocaleDateString('es-CO', { month: 'long', year: 'numeric' });
  }

  recargar(): void {
    const v = this.ctx.selected();
    if (v) this.cargar(v.id);
  }

  private cargar(viviendaId: number): void {
    this.loading.set(true);
    this.error.set(null);
    forkJoin({ est: this.api.estimacion(viviendaId), list: this.api.list(viviendaId) })
      .pipe(
        finalize(() => this.loading.set(false)),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: ({ est, list }) => {
          this.estimacion.set(est);
          this.items.set(list);
          const sel = this.selectedId();
          if (sel != null && !list.some((i) => i.id === sel)) {
            this.cerrarDetalle();
          } else if (sel != null) {
            this.abrirBorrador(sel);
          }
        },
        error: () =>
          this.error.set('No se pudo calcular la estimación. ¿Está levantada la API de electrodomésticos (8083)?'),
      });
  }

  seleccionar(id: number | null): void {
    if (id == null) return;
    if (this.selectedId() === id) {
      this.cerrarDetalle();
      return;
    }
    this.selectedId.set(id);
    this.abrirBorrador(id);
    this.okMsg.set(null);
  }

  cerrarDetalle(): void {
    this.selectedId.set(null);
    this.borrador.set(null);
  }

  /** Vuelve a los datos guardados del electrodoméstico seleccionado. */
  descartar(): void {
    const id = this.selectedId();
    if (id != null) this.abrirBorrador(id);
    this.error.set(null);
  }

  private abrirBorrador(id: number): void {
    const dto = this.items().find((i) => i.id === id);
    if (!dto) return;
    const horarios = (dto.horarios ?? []).map((h) => ({ ...h }));
    const horas = horarios.length ? sum(horarios.map(duracionHoras)) : 168;
    this.borrador.set({
      // Registros anteriores a HAR-20 solo tienen kWh/día: se pasan a W con su horario
      potenciaW: dto.potenciaW ?? (dto.consumoKwhDia > 0 ? Math.round((dto.consumoKwhDia * 1000 * 7) / horas) : null),
      usarAjuste: dto.consumoAjustadoKwhMes != null,
      consumoAjustadoKwhMes: dto.consumoAjustadoKwhMes ?? null,
      esDesplazable: !!dto.esDesplazable,
      activo: dto.activo !== false,
      horarios,
    });
  }

  patch(p: Partial<Borrador>): void {
    this.borrador.update((b) => (b ? { ...b, ...p } : b));
  }

  guardar(): void {
    const v = this.ctx.selected();
    const dto = this.selectedDto();
    const b = this.borrador();
    if (!v || !dto || !b) return;
    if (!b.potenciaW || b.potenciaW <= 0) {
      this.error.set('Indica la potencia en watts (W). Si tu etiqueta dice kWh/mes, usa la calculadora.');
      return;
    }
    if (b.horarios.some((h) => !h.horaInicio || !h.horaFin)) {
      this.error.set('Completa la hora de inicio y fin de cada franja.');
      return;
    }
    if (b.usarAjuste && (b.consumoAjustadoKwhMes == null || b.consumoAjustadoKwhMes < 0)) {
      this.error.set('Indica el consumo mensual ajustado (kWh/mes) o desactiva el ajuste.');
      return;
    }
    const body: ElectrodomesticoUpdatePayload = {
      idTipoPredefinido: dto.idTipoPredefinido,
      idMarcaPredefinida: dto.idMarcaPredefinida,
      marcaOtro: dto.marcaOtro,
      nombre: dto.nombre,
      // El backend lo recalcula con potencia × horario; se envía por compatibilidad
      consumoKwhDia: Math.max(0.0001, Math.round(((b.potenciaW * this.horasSemanaBorrador()) / 7 / 1000) * 10000) / 10000),
      usoSemanal: b.horarios.length ? new Set(b.horarios.map((h) => h.diaSemana)).size : 7,
      horarioHabitual: b.horarios[0]?.horaInicio ?? null,
      esDesplazable: b.esDesplazable,
      activo: b.activo,
      potenciaW: b.potenciaW,
      consumoAjustadoKwhMes: b.usarAjuste ? b.consumoAjustadoKwhMes : null,
      horarios: b.horarios,
    };
    this.saving.set(true);
    this.error.set(null);
    this.api
      .update(v.id, dto.id, body)
      .pipe(
        finalize(() => this.saving.set(false)),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: () => {
          this.okMsg.set(`«${dto.nombre}» actualizado.`);
          this.cargar(v.id);
        },
        error: (e) =>
          this.error.set(e?.error?.message || e?.error?.detail || 'No se pudo guardar el electrodoméstico.'),
      });
  }

  eliminar(): void {
    const v = this.ctx.selected();
    const dto = this.selectedDto();
    if (!v || !dto || !confirm(`¿Eliminar «${dto.nombre}»? Se perderán sus horarios.`)) return;
    this.saving.set(true);
    this.api
      .delete(v.id, dto.id)
      .pipe(
        finalize(() => this.saving.set(false)),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: () => {
          this.cerrarDetalle();
          this.cargar(v.id);
        },
        error: () => this.error.set('No se pudo eliminar.'),
      });
  }

  // ---------------------------------------------------------------- formato
  fmt = fmt;
  hh = hh;

  cop(v: number | null | undefined): string {
    if (v == null) return '—';
    return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v);
  }

  bandaClase(t: TipoHora | null): string {
    return t === 'PICO' ? 'eg-band-pico' : t === 'MEDIA' ? 'eg-band-media' : t === 'VALLE' ? 'eg-band-valle' : '';
  }
}

function hh(h: number): string {
  return `${String(h % 24).padStart(2, '0')}:00`;
}

function fmt(v: number | null | undefined, dec = 1): string {
  if (v == null || Number.isNaN(v)) return '—';
  return v.toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: dec });
}
