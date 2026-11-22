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
      <label class="vs-field">
        <span class="vs-label">Vivienda</span>
        <span class="vs-control">
          <svg class="vs-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M3 10.5 12 3l9 7.5" />
            <path d="M5 9.5V21h14V9.5" />
            <path d="M10 21v-6h4v6" />
          </svg>
          <select
            class="vs-select"
            [value]="ctx.selected()?.id ?? ''"
            (change)="ctx.select(+$any($event.target).value)"
          >
            @for (v of ctx.viviendas(); track v.id) {
              <option [value]="v.id" [selected]="v.id === ctx.selected()?.id">{{ etiqueta(v) }}</option>
            }
          </select>
          <svg class="vs-chevron" viewBox="0 0 24 24" aria-hidden="true"><polyline points="6 9 12 15 18 9" /></svg>
        </span>
      </label>
      <div class="vs-chips">
        @if (ctx.contrato(); as c) {
          <span class="vs-chip vs-chip-ok" title="Los consumos se consultan con este contrato">
            <svg viewBox="0 0 24 24" aria-hidden="true"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" /></svg>
            Contrato {{ c.noContrato }} · {{ c.codComercializadora }}
          </span>
        } @else {
          <a class="vs-chip vs-chip-warn" routerLink="/mi-vivienda">
            <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" /></svg>
            Sin contrato · agregar
          </a>
        }
        @if (!ctx.ubicacion()) {
          <a class="vs-chip vs-chip-warn" routerLink="/mi-vivienda">
            <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" /></svg>
            Sin ciudad · configurar
          </a>
        }
        <ng-content select="[vsChip]" />
      </div>
    } @else if (ctx.loaded()) {
      <div class="vs-field">
        <span class="vs-label">Vivienda</span>
        <a class="vs-empty" routerLink="/mi-vivienda">
          <svg class="vs-empty-icon" viewBox="0 0 24 24" aria-hidden="true"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>
          No tienes viviendas registradas · Registrar vivienda
        </a>
      </div>
    }
  `,
  styles: `
    :host {
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
      min-width: 0;
    }
    /* Dentro del panel de filtros el campo y los chips son celdas de su grilla:
       campo en la fila 1, chips en la fila 2 a todo el ancho */
    :host-context(.dash-filters) {
      display: contents;
    }
    :host-context(.dash-filters) .vs-chips {
      grid-column: 1 / -1;
      grid-row: 2;
    }
    :host-context(.dash-filters) .vs-chips:empty {
      display: none;
    }
    @media (max-width: 899px) {
      :host-context(.dash-filters) .vs-field {
        grid-column: 1 / -1;
      }
    }
    @media (max-width: 559px) {
      :host-context(.dash-filters) .vs-chips {
        grid-row: auto;
      }
    }
    .vs-field {
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
      min-width: 0;
    }
    .vs-label {
      font-size: 0.7rem;
      font-weight: 600;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: var(--color-text-muted);
    }
    .vs-control {
      position: relative;
      display: flex;
      align-items: center;
      min-width: 0;
    }
    .vs-icon,
    .vs-chevron {
      position: absolute;
      width: 1rem;
      height: 1rem;
      fill: none;
      stroke-width: 2;
      stroke-linecap: round;
      stroke-linejoin: round;
      pointer-events: none;
    }
    .vs-icon {
      left: 0.75rem;
      stroke: var(--color-accent);
    }
    .vs-chevron {
      right: 0.7rem;
      stroke: var(--color-text-muted);
    }
    .vs-select {
      appearance: none;
      width: 100%;
      min-width: 0;
      height: 2.5rem;
      padding: 0 2.2rem 0 2.3rem;
      border-radius: 0.6rem;
      border: 1px solid var(--color-border-input);
      background: var(--color-surface-input);
      color: var(--color-text);
      font: inherit;
      font-size: 0.875rem;
      text-overflow: ellipsis;
      cursor: pointer;
      transition: border-color 0.15s, box-shadow 0.15s;
    }
    .vs-select option {
      background: var(--color-bg-solid);
      color: var(--color-text);
    }
    .vs-select:hover {
      border-color: var(--color-accent-border);
    }
    .vs-select:focus-visible {
      outline: none;
      border-color: var(--color-accent);
      box-shadow: 0 0 0 3px var(--color-accent-ring);
    }
    .vs-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 0.35rem;
    }
    .vs-chip {
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
      padding: 0.15rem 0.55rem;
      border-radius: 999px;
      border: 1px solid transparent;
      font-size: 0.72rem;
      font-weight: 500;
      line-height: 1.4;
      text-decoration: none;
      white-space: nowrap;
    }
    .vs-chip svg {
      width: 0.8rem;
      height: 0.8rem;
      fill: none;
      stroke: currentColor;
      stroke-width: 2.25;
      stroke-linecap: round;
      stroke-linejoin: round;
    }
    .vs-chip-ok {
      color: var(--color-success-text);
      background: var(--color-success-soft);
      border-color: color-mix(in srgb, var(--color-success) 35%, transparent);
    }
    .vs-chip-warn {
      color: var(--color-warning-text);
      background: var(--color-warning-soft);
      border-color: color-mix(in srgb, var(--color-warning) 35%, transparent);
      transition: filter 0.15s;
    }
    .vs-chip-warn:hover {
      filter: brightness(1.15);
    }
    .vs-empty {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      height: 2.5rem;
      padding: 0 0.9rem;
      border-radius: 0.6rem;
      border: 1px dashed var(--color-accent-border);
      background: var(--color-accent-soft);
      color: var(--color-accent);
      font-size: 0.875rem;
      font-weight: 500;
      text-decoration: none;
    }
    .vs-empty:hover {
      background: var(--color-accent-soft-hover);
    }
    .vs-empty-icon {
      width: 1rem;
      height: 1rem;
      fill: none;
      stroke: currentColor;
      stroke-width: 2.25;
      stroke-linecap: round;
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
