import { Component, computed, input, output } from '@angular/core';

/** Fecha local en formato YYYY-MM-DD. */
export function fechaLocalYmd(d = new Date()): string {
  const p = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

/** Suma días a una fecha YYYY-MM-DD (en hora local, sin saltos por cambio de horario). */
export function sumarDias(ymd: string, dias: number): string {
  const [y, m, d] = ymd.split('-').map(Number);
  return fechaLocalYmd(new Date(y, m - 1, d + dias));
}

/**
 * Selector de fecha de los filtros (dashboard y tarifas): día anterior / siguiente,
 * calendario nativo y acceso rápido a "Hoy".
 */
@Component({
  selector: 'app-fecha-filtro',
  standalone: true,
  template: `
    <span class="ff-label" [id]="labelId">Fecha</span>
    <div class="ff-row" role="group" [attr.aria-labelledby]="labelId">
      <button type="button" class="ff-step" (click)="mover(-1)" [disabled]="disabled()" aria-label="Día anterior">
        <svg viewBox="0 0 24 24" aria-hidden="true"><polyline points="15 18 9 12 15 6" /></svg>
      </button>
      <span class="ff-control">
        <svg class="ff-icon" viewBox="0 0 24 24" aria-hidden="true">
          <rect x="3" y="4" width="18" height="18" rx="2" />
          <line x1="16" y1="2" x2="16" y2="6" />
          <line x1="8" y1="2" x2="8" y2="6" />
          <line x1="3" y1="10" x2="21" y2="10" />
        </svg>
        <input
          class="ff-input"
          type="date"
          [value]="fecha()"
          [attr.max]="max()"
          [disabled]="disabled()"
          [attr.aria-labelledby]="labelId"
          (change)="elegir($any($event.target).value)"
        />
      </span>
      <button
        type="button"
        class="ff-step"
        (click)="mover(1)"
        [disabled]="disabled() || enMaximo()"
        aria-label="Día siguiente"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true"><polyline points="9 18 15 12 9 6" /></svg>
      </button>
      @if (!esHoy()) {
        <button type="button" class="ff-today" (click)="elegir(hoy())" [disabled]="disabled()">Hoy</button>
      }
    </div>
  `,
  styles: `
    :host {
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
      min-width: 0;
    }
    .ff-label {
      font-size: 0.7rem;
      font-weight: 600;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: var(--color-text-muted);
    }
    .ff-row {
      display: flex;
      align-items: center;
      gap: 0.35rem;
    }
    .ff-control {
      position: relative;
      display: flex;
      align-items: center;
    }
    .ff-icon {
      position: absolute;
      left: 0.7rem;
      width: 1rem;
      height: 1rem;
      fill: none;
      stroke: var(--color-accent);
      stroke-width: 2;
      stroke-linecap: round;
      pointer-events: none;
    }
    .ff-input {
      height: 2.5rem;
      padding: 0 0.6rem 0 2.2rem;
      border-radius: 0.6rem;
      border: 1px solid var(--color-border-input);
      background: var(--color-surface-input);
      color: var(--color-text);
      font: inherit;
      font-size: 0.875rem;
      font-variant-numeric: tabular-nums;
      color-scheme: light dark;
      transition: border-color 0.15s, box-shadow 0.15s;
    }
    :host-context([data-theme='dark']) .ff-input {
      color-scheme: dark;
    }
    :host-context([data-theme='light']) .ff-input {
      color-scheme: light;
    }
    .ff-input:hover:not(:disabled) {
      border-color: var(--color-accent-border);
    }
    .ff-input:focus-visible {
      outline: none;
      border-color: var(--color-accent);
      box-shadow: 0 0 0 3px var(--color-accent-ring);
    }
    .ff-step,
    .ff-today {
      height: 2.5rem;
      border-radius: 0.6rem;
      border: 1px solid var(--color-border-input);
      background: var(--color-surface-2);
      color: var(--color-text-muted);
      cursor: pointer;
      transition: border-color 0.15s, background 0.15s, color 0.15s;
    }
    .ff-step {
      display: grid;
      place-items: center;
      width: 2.25rem;
      padding: 0;
    }
    .ff-step svg {
      width: 1rem;
      height: 1rem;
      fill: none;
      stroke: currentColor;
      stroke-width: 2.25;
      stroke-linecap: round;
      stroke-linejoin: round;
    }
    .ff-today {
      padding: 0 0.8rem;
      font: inherit;
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--color-accent);
      border-color: var(--color-accent-border);
      background: var(--color-accent-soft);
    }
    .ff-step:hover:not(:disabled),
    .ff-today:hover:not(:disabled) {
      border-color: var(--color-accent-border);
      background: var(--color-accent-soft-hover);
      color: var(--color-accent);
    }
    .ff-step:focus-visible,
    .ff-today:focus-visible {
      outline: none;
      box-shadow: 0 0 0 3px var(--color-accent-ring);
    }
    .ff-step:disabled,
    .ff-today:disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }
  `,
})
export class FechaFiltroComponent {
  private static nextId = 0;

  /** Fecha seleccionada (YYYY-MM-DD). */
  readonly fecha = input.required<string>();
  /** Fecha máxima seleccionable (YYYY-MM-DD); sin valor no hay límite. */
  readonly max = input<string | null>(null);
  readonly disabled = input(false);
  readonly fechaChange = output<string>();

  readonly labelId = `fecha-filtro-${FechaFiltroComponent.nextId++}`;
  readonly hoy = () => fechaLocalYmd();
  readonly esHoy = computed(() => this.fecha() === this.hoy());
  readonly enMaximo = computed(() => {
    const max = this.max();
    return max != null && this.fecha() >= max;
  });

  mover(dias: number): void {
    this.elegir(sumarDias(this.fecha(), dias));
  }

  elegir(valor: string): void {
    const max = this.max();
    if (!valor || valor === this.fecha() || (max != null && valor > max)) {
      return;
    }
    this.fechaChange.emit(valor);
  }
}
