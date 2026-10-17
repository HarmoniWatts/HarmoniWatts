import { computed, inject, Injectable, signal } from '@angular/core';
import { Observable, of } from 'rxjs';
import { catchError, finalize, tap } from 'rxjs/operators';
import type { UbicacionTarifaria } from '../tarifas/tarifas.models';
import type { ViviendaDto } from './vivienda.service';
import { ViviendaService } from './vivienda.service';

const STORAGE_KEY = 'hw.viviendaSeleccionada';

/**
 * Vivienda activa compartida por el dashboard, el módulo de tarifas y la barra lateral.
 * La selección se recuerda en el navegador (solo es una preferencia de vista).
 */
@Injectable({ providedIn: 'root' })
export class ViviendaContextService {
  private readonly api = inject(ViviendaService);

  readonly viviendas = signal<ViviendaDto[]>([]);
  readonly loading = signal(false);
  readonly loaded = signal(false);
  readonly error = signal<string | null>(null);
  private readonly selectedId = signal<number | null>(readStoredId());

  readonly selected = computed<ViviendaDto | null>(() => {
    const list = this.viviendas();
    return list.find((v) => v.id === this.selectedId()) ?? list[0] ?? null;
  });

  /** Ciudad + mercado + estrato de la vivienda activa; null si aún no tiene ciudad. */
  readonly ubicacion = computed<UbicacionTarifaria | null>(() => toUbicacion(this.selected()));

  /** Carga las viviendas del usuario (una vez por sesión salvo `force`). */
  load(force = false): Observable<ViviendaDto[]> {
    if (this.loaded() && !force) {
      return of(this.viviendas());
    }
    this.loading.set(true);
    this.error.set(null);
    return this.api.list().pipe(
      tap((rows) => {
        this.viviendas.set(rows);
        this.loaded.set(true);
      }),
      catchError(() => {
        this.error.set('No se pudieron cargar tus viviendas.');
        return of([] as ViviendaDto[]);
      }),
      finalize(() => this.loading.set(false)),
    );
  }

  select(id: number): void {
    this.selectedId.set(id);
    try {
      localStorage.setItem(STORAGE_KEY, String(id));
    } catch {
      // almacenamiento no disponible (modo privado): la selección dura solo esta sesión
    }
  }

  /** Tras crear/editar/eliminar en "Mi vivienda". */
  setViviendas(rows: ViviendaDto[]): void {
    this.viviendas.set(rows);
    this.loaded.set(true);
  }
}

export function toUbicacion(v: ViviendaDto | null | undefined): UbicacionTarifaria | null {
  if (!v || v.idZona == null || !v.codMercado || v.estrato == null) {
    return null;
  }
  return { idZona: v.idZona, codMercado: v.codMercado, estrato: v.estrato };
}

function readStoredId(): number | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? Number(raw) || null : null;
  } catch {
    return null;
  }
}
