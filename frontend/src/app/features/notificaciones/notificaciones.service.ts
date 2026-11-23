import { computed, DestroyRef, effect, inject, Injectable, signal, untracked } from '@angular/core';
import { forkJoin, of, Subscription, timer } from 'rxjs';
import { catchError, map, switchMap } from 'rxjs/operators';
import type { AlertSeverity, AlertType, DashboardAlert, RecommendationItem } from '../dashboard/dashboard.models';
import { DashboardService } from '../dashboard/dashboard.service';
import { ViviendaContextService } from '../vivienda/vivienda-context.service';
import { environment } from '../../../environments/environment';

/** Una notificación: alerta (HAR-21) o recomendación IA. */
export interface Notificacion {
  id: string;
  origen: 'ALERTA' | 'IA';
  tipo: AlertType | 'RECOMMENDATION';
  severidad: AlertSeverity | null;
  titulo: string;
  mensaje: string;
  /** Hora local 'YYYY-MM-DDTHH:mm[:ss]' (las de IA: momento en que se cargaron). */
  fecha: string;
}

const LEIDAS_KEY = 'hw.notificaciones.leidas';
const AVISADAS_KEY = 'hw.notificaciones.avisadas';
/** Las alertas cambian con la hora (franja) y con cada lectura nueva (consumo). */
const REFRESCO_MS = 5 * 60 * 1000;
const ORDEN: Record<string, number> = { HIGH: 0, MEDIUM: 1, LOW: 2 };

export function desdeAlerta(a: DashboardAlert): Notificacion {
  return { id: a.id, origen: 'ALERTA', tipo: a.type, severidad: a.severity, titulo: a.title, mensaje: a.message, fecha: a.timestamp };
}

export function desdeRecomendacion(r: RecommendationItem, fecha: string): Notificacion {
  return {
    id: `ia-${r.id}`,
    origen: 'IA',
    tipo: 'RECOMMENDATION',
    severidad: null,
    titulo: r.title,
    mensaje: r.body,
    fecha,
  };
}

/** Alertas primero (más graves y recientes arriba); después las recomendaciones IA. */
export function ordenarNotificaciones(ns: Notificacion[]): Notificacion[] {
  return [...ns].sort((a, b) => {
    if (a.origen !== b.origen) return a.origen === 'ALERTA' ? -1 : 1;
    return (ORDEN[a.severidad ?? ''] ?? 3) - (ORDEN[b.severidad ?? ''] ?? 3) || b.fecha.localeCompare(a.fecha);
  });
}

/**
 * Notificaciones de la vivienda activa: alertas visuales (HAR-21) y recomendaciones IA.
 * Las comparten la campana del menú, el aviso emergente y la tarjeta del dashboard.
 * Leídas / avisadas se recuerdan en el navegador (solo preferencia de vista).
 */
@Injectable({ providedIn: 'root' })
export class NotificacionesService {
  private readonly api = inject(DashboardService);
  private readonly ctx = inject(ViviendaContextService);

  readonly items = signal<Notificacion[]>([]);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly panelAbierto = signal(false);
  /** Alerta importante nueva para mostrar como aviso emergente. */
  readonly aviso = signal<Notificacion | null>(null);

  private readonly leidas = signal<Set<string>>(leerSet(LEIDAS_KEY));
  readonly noLeidas = computed(() => this.items().filter((n) => !this.leidas().has(n.id)).length);

  private sub: Subscription | null = null;
  private iniciado = false;

  /** Arranca la carga periódica (una sola vez; la llama el layout autenticado). */
  iniciar(destroyRef: DestroyRef): void {
    if (this.iniciado) return;
    this.iniciado = true;
    const ref = effect(() => {
      const contrato = this.ctx.contrato();
      const ubicacion = this.ctx.ubicacion();
      this.ctx.selected();
      untracked(() => this.programar(contrato, ubicacion));
    });
    destroyRef.onDestroy(() => {
      ref.destroy();
      this.sub?.unsubscribe();
      this.iniciado = false;
    });
  }

  recargar(): void {
    this.programar(this.ctx.contrato(), this.ctx.ubicacion());
  }

  esLeida(id: string): boolean {
    return this.leidas().has(id);
  }

  marcarLeida(id: string): void {
    const s = new Set(this.leidas());
    s.add(id);
    this.guardarLeidas(s);
    if (this.aviso()?.id === id) this.aviso.set(null);
  }

  marcarTodasLeidas(): void {
    const s = new Set(this.leidas());
    this.items().forEach((n) => s.add(n.id));
    this.guardarLeidas(s);
    this.aviso.set(null);
  }

  abrirPanel(): void {
    this.panelAbierto.set(true);
    this.aviso.set(null);
  }

  private programar(
    contrato: { noContrato: string; codComercializadora: string } | null,
    ubicacion: { idZona: number; codMercado: string; estrato: number } | null,
  ): void {
    this.sub?.unsubscribe();
    this.items.set([]);
    this.error.set(null);
    if (!contrato && !ubicacion) return;
    this.sub = timer(0, REFRESCO_MS)
      .pipe(
        switchMap(() => {
          this.loading.set(true);
          const alertas$ = this.api
            .getAlerts({ ...(contrato ?? {}), ...(ubicacion ?? {}), at: horaSimulada() ?? undefined })
            .pipe(map((r) => r.alerts.map(desdeAlerta)));
          const ia$ = contrato
            ? this.api
                .getRecommendations({ ...contrato, limit: 3 })
                .pipe(
                  map((r) => r.items.map((x) => desdeRecomendacion(x, ahoraLocal()))),
                  catchError(() => of([] as Notificacion[])),
                )
            : of([] as Notificacion[]);
          return forkJoin({ alertas: alertas$, ia: ia$ }).pipe(
            catchError(() => {
              this.error.set('No se pudieron cargar las alertas.');
              return of({ alertas: [] as Notificacion[], ia: [] as Notificacion[] });
            }),
          );
        }),
      )
      .subscribe(({ alertas, ia }) => {
        this.loading.set(false);
        this.items.set(ordenarNotificaciones([...alertas, ...ia]));
        this.avisarNuevas(alertas);
      });
  }

  /** Aviso emergente para la alerta media/alta más grave que aún no se haya avisado ni leído. */
  private avisarNuevas(alertas: Notificacion[]): void {
    const avisadas = leerSet(AVISADAS_KEY, sessionStorage);
    const nueva = alertas.find(
      (a) => (a.severidad === 'HIGH' || a.severidad === 'MEDIUM') && !avisadas.has(a.id) && !this.leidas().has(a.id),
    );
    if (!nueva) return;
    avisadas.add(nueva.id);
    guardarSet(AVISADAS_KEY, avisadas, sessionStorage);
    this.aviso.set(nueva);
  }

  private guardarLeidas(s: Set<string>): void {
    // Solo se conservan las leídas que siguen vigentes, para que la lista no crezca sin fin
    const vigentes = new Set(this.items().map((n) => n.id));
    const recortado = new Set([...s].filter((id) => vigentes.has(id)));
    this.leidas.set(recortado);
    guardarSet(LEIDAS_KEY, recortado);
  }
}

/** Solo en desarrollo: ?simularHora=2026-11-22T19:00 en la URL para probar las alertas de franja. */
function horaSimulada(): string | null {
  if (environment.production) return null;
  try {
    const v = new URLSearchParams(window.location.search).get('simularHora');
    return v && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(v) ? v : null;
  } catch {
    return null;
  }
}

function ahoraLocal(): string {
  const d = new Date();
  const p = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
}

function leerSet(key: string, storage: Storage = localStorage): Set<string> {
  try {
    const raw = storage.getItem(key);
    return new Set(raw ? (JSON.parse(raw) as string[]) : []);
  } catch {
    return new Set();
  }
}

function guardarSet(key: string, s: Set<string>, storage: Storage = localStorage): void {
  try {
    storage.setItem(key, JSON.stringify([...s]));
  } catch {
    // almacenamiento no disponible (modo privado): dura solo esta sesión
  }
}
