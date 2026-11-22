import { Component, computed, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DIAS_POR_MES, POTENCIA_TIPICA_W } from '../gestion/estimacion.util';

/** W equivalentes a un consumo mensual repartido en `horasSemana` de uso. */
export function wattsDesdeKwhMes(kwhMes: number, horasSemana: number): number | null {
  if (!(kwhMes > 0) || !(horasSemana > 0)) return null;
  const horasMes = (horasSemana * DIAS_POR_MES) / 7;
  return Math.round((kwhMes * 1000) / horasMes);
}

/** kWh/mes que consume `w` vatios usados `horasSemana` horas por semana. */
export function kwhMesDesdeWatts(w: number, horasSemana: number): number {
  return ((w * horasSemana) / 1000) * (DIAS_POR_MES / 7);
}

/** Aparatos con compresor: la placa da el pico, no el promedio; mejor el kWh/mes de la etiqueta. */
export const TIPOS_CON_COMPRESOR = ['NEVERA', 'CONGELADOR', 'AIRE_ACONDICIONADO'];

/**
 * Elige la potencia a usar con lo que leyó la IA: la de la placa, salvo en aparatos con compresor
 * (o si no hay placa), donde se convierte el kWh/mes de la etiqueta según el horario.
 */
export function potenciaDesdeEtiqueta(
  potenciaW: number | null | undefined,
  kwhMes: number | null | undefined,
  tipoCodigo: string | null | undefined,
  horasSemana: number,
): { w: number; origen: 'placa' | 'etiqueta' } | null {
  const placa = potenciaW && potenciaW > 0 ? Math.round(potenciaW) : null;
  const etiqueta = kwhMes && kwhMes > 0 ? wattsDesdeKwhMes(kwhMes, horasSemana) : null;
  const preferirEtiqueta = TIPOS_CON_COMPRESOR.includes(tipoCodigo ?? '');
  if (etiqueta != null && (preferirEtiqueta || placa == null)) return { w: etiqueta, origen: 'etiqueta' };
  if (placa != null) return { w: placa, origen: 'placa' };
  return null;
}

/**
 * Potencia del electrodoméstico en W (dato único de consumo, HAR-20) con una calculadora para
 * convertir el kWh/mes de la etiqueta energética según el horario de uso.
 */
@Component({
  selector: 'app-potencia-input',
  standalone: true,
  imports: [FormsModule],
  template: `
    <div class="pi-label-row">
      <span class="pi-label">Potencia (W) <span class="pi-req">*</span></span>
      <button
        type="button"
        class="pi-calc-btn"
        [class.pi-calc-btn-on]="abierta()"
        (click)="abierta.set(!abierta())"
        [attr.aria-expanded]="abierta()"
        title="Convertir kWh/mes a watts"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <rect x="5" y="2.5" width="14" height="19" rx="2" />
          <rect x="8" y="5.5" width="8" height="3.5" rx="0.6" />
          <line x1="8.5" y1="12.5" x2="8.51" y2="12.5" />
          <line x1="12" y1="12.5" x2="12.01" y2="12.5" />
          <line x1="15.5" y1="12.5" x2="15.51" y2="12.5" />
          <line x1="8.5" y1="16.5" x2="8.51" y2="16.5" />
          <line x1="12" y1="16.5" x2="12.01" y2="16.5" />
          <line x1="15.5" y1="16.5" x2="15.51" y2="16.5" />
        </svg>
        <span>Calculadora</span>
      </button>
    </div>
    <input
      class="pi-input"
      type="number"
      min="1"
      step="1"
      [name]="name() + 'potenciaW'"
      [ngModel]="potenciaW()"
      (ngModelChange)="potenciaWChange.emit($event)"
      [placeholder]="tipica() ? 'Ej. ' + tipica() : 'Ej. 500'"
    />
    <span class="pi-help">
      Viene en la placa o etiqueta del aparato.
      @if (tipica(); as t) {
        @if (potenciaW() !== t) {
          <button type="button" class="pi-link" (click)="potenciaWChange.emit(t)">Usar valor típico ({{ t }} W)</button>
        }
      }
    </span>
    @if (estimadoMes(); as m) {
      <span class="pi-estimado">
        Con tu horario: <strong>≈ {{ fmt(m, 1) }} kWh/mes</strong> ({{ fmt(horasSemana(), 1) }} h/semana)
      </span>
    }

    @if (abierta()) {
      <div class="pi-calc">
        <span class="pi-calc-title">¿Tu etiqueta dice kWh/mes?</span>
        <p class="pi-calc-text">
          Neveras, aires y lavadoras traen la etiqueta energética con el consumo mensual. Lo convertimos a
          watts según el horario que indicaste ({{ fmt(horasSemana(), 1) }} h/semana).
        </p>
        <div class="pi-calc-row">
          <label class="pi-calc-field">
            <span>kWh/mes</span>
            <input
              class="pi-input"
              type="number"
              min="0.1"
              step="0.1"
              [name]="name() + 'calcKwhMes'"
              [ngModel]="kwhMes()"
              (ngModelChange)="kwhMes.set($event)"
              placeholder="Ej. 35"
            />
          </label>
          <span class="pi-calc-eq">=</span>
          <span class="pi-calc-res">
            <strong>{{ resultado() != null ? resultado() + ' W' : '—' }}</strong>
            <small>potencia promedio</small>
          </span>
          <button type="button" class="pi-apply" (click)="aplicar()" [disabled]="resultado() == null">Aplicar</button>
        </div>
        @if (!(horasSemana() > 0)) {
          <p class="pi-calc-warn">Primero indica el horario de uso.</p>
        }
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
    .pi-label-row {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .pi-label {
      font-size: 0.875rem;
      font-weight: 600;
      color: var(--color-text-strong);
    }
    .pi-req {
      color: var(--color-text-muted);
    }
    .pi-calc-btn {
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
      height: 1.7rem;
      padding: 0 0.6rem 0 0.45rem;
      border-radius: 999px;
      border: 1px solid var(--color-accent-border);
      background: var(--color-accent-soft);
      color: var(--color-accent);
      font: inherit;
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s, color 0.15s;
    }
    .pi-calc-btn svg {
      width: 0.95rem;
      height: 0.95rem;
      fill: none;
      stroke: currentColor;
      stroke-width: 1.9;
      stroke-linecap: round;
      stroke-linejoin: round;
    }
    .pi-calc-btn:hover,
    .pi-calc-btn-on {
      background: var(--color-accent);
      color: var(--color-text-on-accent);
    }
    .pi-input {
      height: 2.6rem;
      min-width: 0;
      padding: 0 0.8rem;
      border-radius: 0.6rem;
      border: 1px solid var(--color-border-input);
      background: var(--color-surface-input);
      color: var(--color-text);
      font: inherit;
      font-size: 0.9rem;
    }
    .pi-input:focus-visible {
      outline: none;
      border-color: var(--color-accent);
      box-shadow: 0 0 0 3px var(--color-accent-ring);
    }
    .pi-help {
      display: flex;
      flex-wrap: wrap;
      gap: 0.25rem 0.6rem;
      font-size: 0.76rem;
      color: var(--color-text-subtle);
    }
    .pi-link {
      padding: 0;
      border: 0;
      background: none;
      color: var(--color-accent);
      font: inherit;
      cursor: pointer;
    }
    .pi-link:hover {
      text-decoration: underline;
    }
    .pi-estimado {
      font-size: 0.8rem;
      color: var(--color-text-muted);
    }
    .pi-estimado strong {
      color: var(--color-text-strong);
    }
    .pi-calc {
      margin-top: 0.35rem;
      padding: 0.75rem 0.85rem;
      border-radius: 0.7rem;
      border: 1px solid var(--color-border);
      background: var(--color-surface-2);
    }
    .pi-calc-title {
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--color-text-strong);
    }
    .pi-calc-text {
      margin: 0.25rem 0 0.65rem;
      font-size: 0.8rem;
      line-height: 1.4;
      color: var(--color-text-muted);
    }
    .pi-calc-row {
      display: flex;
      flex-wrap: wrap;
      align-items: flex-end;
      gap: 0.6rem;
    }
    .pi-calc-field {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
      width: 7.5rem;
      font-size: 0.75rem;
      color: var(--color-text-muted);
    }
    .pi-calc-eq {
      padding-bottom: 0.65rem;
      color: var(--color-text-muted);
    }
    .pi-calc-res {
      display: flex;
      flex-direction: column;
      padding-bottom: 0.25rem;
      min-width: 5rem;
    }
    .pi-calc-res strong {
      font-size: 1.05rem;
      color: var(--color-text-strong);
    }
    .pi-calc-res small {
      font-size: 0.7rem;
      color: var(--color-text-subtle);
    }
    .pi-apply {
      height: 2.4rem;
      padding: 0 0.9rem;
      border-radius: 0.55rem;
      border: 1px solid var(--color-accent-border);
      background: var(--color-accent-soft);
      color: var(--color-accent);
      font: inherit;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
    }
    .pi-apply:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    .pi-calc-warn {
      margin: 0.5rem 0 0;
      font-size: 0.78rem;
      color: var(--color-warning-text);
    }
  `,
})
export class PotenciaInputComponent {
  readonly potenciaW = input<number | null>(null);
  /** Horas de uso por semana según el horario (168 = siempre encendido). */
  readonly horasSemana = input(0);
  readonly tipoCodigo = input<string | null>(null);
  readonly name = input('pi');
  readonly potenciaWChange = output<number | null>();

  readonly abierta = signal(false);
  readonly kwhMes = signal<number | null>(null);

  readonly tipica = computed(() => POTENCIA_TIPICA_W[this.tipoCodigo() ?? ''] ?? null);
  readonly resultado = computed(() => wattsDesdeKwhMes(this.kwhMes() ?? 0, this.horasSemana()));
  readonly estimadoMes = computed(() => {
    const w = this.potenciaW();
    return w && w > 0 && this.horasSemana() > 0 ? kwhMesDesdeWatts(w, this.horasSemana()) : null;
  });

  aplicar(): void {
    const r = this.resultado();
    if (r == null) return;
    this.potenciaWChange.emit(r);
    this.abierta.set(false);
  }

  fmt(v: number, dec: number): string {
    return v.toLocaleString('es-CO', { maximumFractionDigits: dec });
  }
}
