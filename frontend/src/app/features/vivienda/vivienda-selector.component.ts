import { Component, computed, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { TarifasService } from '../tarifas/tarifas.service';
import { ViviendaContextService } from './vivienda-context.service';
import type { ViviendaDto } from './vivienda.service';

/** Selector de la vivienda activa (dashboard y tarifas). */
@Component({
  selector: 'app-vivienda-selector',
  standalone: true,
  imports: [RouterLink],
  template: `
    @if (ctx.viviendas().length) {
      <label class="vs-label">
        <span>Vivienda</span>
        <select
          class="vs-select"
          [value]="ctx.selected()?.id ?? ''"
          (change)="ctx.select(+$any($event.target).value)"
        >
          @for (v of ctx.viviendas(); track v.id) {
            <option [value]="v.id" [selected]="v.id === ctx.selected()?.id">{{ etiqueta(v) }}</option>
          }
        </select>
      </label>
      @if (!ctx.ubicacion()) {
        <span class="vs-warn">
          Esta vivienda no tiene ciudad configurada.
          <a routerLink="/mi-vivienda">Configúrala en Mi vivienda</a>
        </span>
      }
    } @else if (ctx.loaded()) {
      <span class="vs-warn">
        No tienes viviendas registradas. <a routerLink="/mi-vivienda">Registrar vivienda</a>
      </span>
    }
  `,
  styles: `
    :host {
      display: flex;
      flex-wrap: wrap;
      align-items: flex-end;
      gap: 0.75rem;
    }
    .vs-label {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
      font-size: 0.75rem;
      color: var(--color-text-muted);
    }
    .vs-select {
      width: 100%;
      min-width: 16rem;
      max-width: 32rem;
      border-radius: 0.5rem;
      border: 1px solid var(--color-border-input);
      background: var(--color-surface-input);
      color: var(--color-text);
      padding: 0.35rem 0.5rem;
    }
    @media (max-width: 639px) {
      :host,
      .vs-label {
        flex: 1 1 100%;
      }
      .vs-select {
        min-width: 0;
        max-width: none;
      }
    }
    .vs-warn {
      font-size: 0.8rem;
      color: var(--color-warning-text);
    }
    .vs-warn a {
      color: var(--color-accent);
    }
  `,
})
export class ViviendaSelectorComponent {
  protected readonly ctx = inject(ViviendaContextService);
  private readonly ciudades = toSignal(
    inject(TarifasService)
      .listCiudades()
      .pipe(catchError(() => of([]))),
    { initialValue: [] },
  );
  private readonly municipioPorZona = computed(
    () => new Map(this.ciudades().map((c) => [`${c.id_zona}|${c.cod_mercado}`, c.municipio])),
  );

  constructor() {
    this.ctx.load().subscribe();
  }

  etiqueta(v: ViviendaDto): string {
    const ciudad = this.municipioPorZona().get(`${v.idZona}|${v.codMercado}`);
    return `${v.tipo} · ${v.ubicacion}${ciudad ? ` · ${ciudad}` : ''} · E${v.estrato}`;
  }
}
