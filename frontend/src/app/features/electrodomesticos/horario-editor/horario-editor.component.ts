import { Component, computed, input, output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import type { HorarioUso } from '../electrodomesticos.service';
import { DIAS_LARGOS, duracionHoras, sum } from '../gestion/estimacion.util';

/** Franja por defecto al empezar a definir horarios. */
export const FRANJA_DEFECTO: HorarioUso = { diaSemana: 1, horaInicio: '18:00', horaFin: '19:00' };

/**
 * Editor de franjas de uso semanales (HAR-20). Sin franjas = «siempre encendido»: el consumo
 * diario se reparte en las 24 h de todos los días.
 */
@Component({
  selector: 'app-horario-editor',
  standalone: true,
  imports: [FormsModule],
  template: `
    <div class="he-head">
      <label class="he-switch">
        <input type="checkbox" [checked]="siempre()" (change)="toggleSiempre($any($event.target).checked)" />
        <span>Siempre encendido <small>(24 h, todos los días: nevera, router…)</small></span>
      </label>
      @if (!siempre()) {
        <span class="he-total">{{ horasSemana().toLocaleString('es-CO', { maximumFractionDigits: 1 }) }} h/semana</span>
      }
    </div>

    @if (!siempre()) {
      @for (h of horarios(); track $index; let i = $index) {
        <div class="he-franja">
          <select class="he-input" [ngModel]="h.diaSemana" (ngModelChange)="editar(i, { diaSemana: +$event })" [name]="name() + 'dia' + i" aria-label="Día">
            @for (d of dias; track $index) {
              <option [ngValue]="$index + 1">{{ d }}</option>
            }
          </select>
          <input class="he-input" type="time" [ngModel]="h.horaInicio" (ngModelChange)="editar(i, { horaInicio: $event })" [name]="name() + 'ini' + i" aria-label="Desde" />
          <span class="he-sep">a</span>
          <input class="he-input" type="time" [ngModel]="h.horaFin" (ngModelChange)="editar(i, { horaFin: $event })" [name]="name() + 'fin' + i" aria-label="Hasta" />
          <span class="he-actions">
            <button type="button" class="he-chip" (click)="replicar(i, [1, 2, 3, 4, 5])" title="Copiar a lunes–viernes">L–V</button>
            <button type="button" class="he-chip" (click)="replicar(i, [6, 7])" title="Copiar a sábado y domingo">S–D</button>
            <button type="button" class="he-chip" (click)="replicar(i, [1, 2, 3, 4, 5, 6, 7])" title="Copiar a todos los días">Todos</button>
            <button type="button" class="he-x" (click)="quitar(i)" aria-label="Quitar franja">
              <svg viewBox="0 0 24 24" aria-hidden="true"><line x1="6" y1="6" x2="18" y2="18" /><line x1="18" y1="6" x2="6" y2="18" /></svg>
            </button>
          </span>
        </div>
      }
      <button type="button" class="he-add" (click)="agregar()">+ Agregar franja</button>
      <p class="he-help">Si la hora final es menor que la inicial, la franja sigue después de medianoche (p. ej. 22:00 a 02:00).</p>
    }
  `,
  styles: `
    :host {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      min-width: 0;
      /* La fila se adapta al ancho del formulario, no al de la ventana */
      container-type: inline-size;
    }
    .he-head {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 0.5rem;
    }
    .he-switch {
      display: inline-flex;
      align-items: flex-start;
      gap: 0.5rem;
      font-size: 0.875rem;
      color: var(--color-text);
      cursor: pointer;
    }
    .he-switch small {
      color: var(--color-text-subtle);
    }
    .he-switch input {
      width: 1rem;
      height: 1rem;
      margin-top: 0.15rem;
      accent-color: var(--color-accent);
    }
    .he-total {
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--color-text-muted);
    }
    .he-franja {
      display: grid;
      grid-template-columns: minmax(8rem, 1fr) minmax(6.5rem, 8rem) auto minmax(6.5rem, 8rem) auto;
      align-items: center;
      gap: 0.5rem;
      padding: 0.5rem;
      border-radius: 0.7rem;
      background: var(--color-surface-2);
    }
    .he-input {
      height: 2.4rem;
      min-width: 0;
      padding: 0 0.7rem;
      border-radius: 0.55rem;
      border: 1px solid var(--color-border-input);
      background: var(--color-surface-input);
      color: var(--color-text);
      font: inherit;
      font-size: 0.875rem;
    }
    .he-input:focus-visible {
      outline: none;
      border-color: var(--color-accent);
      box-shadow: 0 0 0 3px var(--color-accent-ring);
    }
    select.he-input option {
      background: var(--color-bg-solid);
      color: var(--color-text);
    }
    .he-sep {
      font-size: 0.8rem;
      color: var(--color-text-muted);
    }
    .he-actions {
      display: inline-flex;
      align-items: center;
      justify-content: flex-end;
      gap: 0.3rem;
    }
    .he-chip,
    .he-x {
      height: 2rem;
      padding: 0 0.55rem;
      border-radius: 0.5rem;
      border: 1px solid var(--color-border-input);
      background: var(--color-surface-elev);
      color: var(--color-text-muted);
      font: inherit;
      font-size: 0.75rem;
      font-weight: 600;
      white-space: nowrap;
      cursor: pointer;
    }
    .he-chip:hover {
      color: var(--color-accent);
      border-color: var(--color-accent-border);
    }
    .he-x {
      display: inline-grid;
      place-items: center;
      width: 2rem;
      padding: 0;
    }
    .he-x svg {
      width: 0.85rem;
      height: 0.85rem;
      fill: none;
      stroke: currentColor;
      stroke-width: 2.25;
      stroke-linecap: round;
    }
    .he-x:hover {
      color: var(--color-danger-text);
      border-color: var(--color-danger);
    }
    .he-add {
      align-self: flex-start;
      height: 2.2rem;
      padding: 0 0.9rem;
      border-radius: 0.55rem;
      border: 1px dashed var(--color-accent-border);
      background: var(--color-accent-soft);
      color: var(--color-accent);
      font: inherit;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
    }
    .he-add:hover {
      background: var(--color-accent-soft-hover);
    }
    .he-help {
      margin: 0;
      font-size: 0.75rem;
      color: var(--color-text-subtle);
    }
    @container (max-width: 640px) {
      .he-franja {
        grid-template-columns: 1fr auto 1fr;
      }
      .he-franja > select {
        grid-column: 1 / -1;
      }
      .he-actions {
        grid-column: 1 / -1;
        justify-content: flex-start;
      }
    }
  `,
})
export class HorarioEditorComponent {
  readonly horarios = input.required<HorarioUso[]>();
  /** Prefijo de los `name` de los controles (varios editores en una misma página). */
  readonly name = input('he');
  readonly horariosChange = output<HorarioUso[]>();

  readonly dias = DIAS_LARGOS;
  readonly siempre = computed(() => this.horarios().length === 0);
  readonly horasSemana = computed(() => sum(this.horarios().map(duracionHoras)));

  toggleSiempre(siempre: boolean): void {
    this.horariosChange.emit(siempre ? [] : [{ ...FRANJA_DEFECTO }]);
  }

  agregar(): void {
    const ultimo = this.horarios().at(-1);
    const nueva = ultimo ? { ...ultimo, diaSemana: (ultimo.diaSemana % 7) + 1 } : { ...FRANJA_DEFECTO };
    this.horariosChange.emit([...this.horarios(), nueva]);
  }

  editar(i: number, p: Partial<HorarioUso>): void {
    this.horariosChange.emit(this.horarios().map((h, j) => (j === i ? { ...h, ...p } : h)));
  }

  quitar(i: number): void {
    const resto = this.horarios().filter((_, j) => j !== i);
    // Quitar la última franja no debe convertirlo en «siempre encendido» sin querer
    this.horariosChange.emit(resto.length ? resto : [{ ...FRANJA_DEFECTO }]);
  }

  /** Copia la franja a otros días sin duplicar las que ya existen. */
  replicar(i: number, dias: number[]): void {
    const hs = this.horarios();
    const base = hs[i];
    if (!base) return;
    const existe = (d: number) =>
      hs.some((h) => h.diaSemana === d && h.horaInicio === base.horaInicio && h.horaFin === base.horaFin);
    const nuevas = dias.filter((d) => !existe(d)).map((d) => ({ ...base, diaSemana: d }));
    this.horariosChange.emit(
      [...hs, ...nuevas].sort((a, b) => a.diaSemana - b.diaSemana || a.horaInicio.localeCompare(b.horaInicio)),
    );
  }
}
