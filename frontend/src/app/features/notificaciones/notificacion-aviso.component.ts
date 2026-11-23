import { Component, effect, inject, OnDestroy } from '@angular/core';
import { NotificacionesService } from './notificaciones.service';

const DURACION_MS = 12000;

/** Aviso emergente cuando aparece una alerta media o alta nueva (HAR-21). */
@Component({
  selector: 'app-notificacion-aviso',
  standalone: true,
  template: `
    @if (svc.aviso(); as a) {
      <div class="na {{ a.severidad === 'HIGH' ? 'na-alta' : 'na-media' }}" role="alert">
        <span class="na-ic" aria-hidden="true">
          <svg viewBox="0 0 24 24"><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" /><line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" /></svg>
        </span>
        <button type="button" class="na-body" (click)="svc.abrirPanel()">
          <strong>{{ a.titulo }}</strong>
          <span>{{ a.mensaje }}</span>
          <small>Ver notificaciones</small>
        </button>
        <button type="button" class="na-x" (click)="svc.aviso.set(null)" aria-label="Cerrar aviso">
          <svg viewBox="0 0 24 24"><line x1="6" y1="6" x2="18" y2="18" /><line x1="18" y1="6" x2="6" y2="18" /></svg>
        </button>
      </div>
    }
  `,
  styles: `
    .na {
      position: fixed;
      top: 4rem;
      right: 1rem;
      z-index: 55;
      display: flex;
      gap: 0.65rem;
      width: min(24rem, calc(100vw - 2rem));
      padding: 0.8rem 0.8rem 0.8rem 0.9rem;
      border-radius: 0.9rem;
      border: 1px solid;
      background: var(--color-bg-solid);
      box-shadow: 0 14px 40px rgba(0, 0, 0, 0.35);
      animation: na-in 0.25s ease-out;
    }
    @keyframes na-in {
      from {
        opacity: 0;
        transform: translateY(-0.5rem);
      }
    }
    .na-alta {
      border-color: color-mix(in srgb, var(--color-danger) 55%, transparent);
    }
    .na-media {
      border-color: color-mix(in srgb, var(--color-warning) 55%, transparent);
    }
    .na-ic {
      display: inline-grid;
      place-items: center;
      flex-shrink: 0;
      width: 2rem;
      height: 2rem;
      border-radius: 0.6rem;
    }
    .na-alta .na-ic {
      color: var(--color-danger-text);
      background: var(--color-danger-soft);
    }
    .na-media .na-ic {
      color: var(--color-warning-text);
      background: var(--color-warning-soft);
    }
    .na-ic svg,
    .na-x svg {
      width: 1rem;
      height: 1rem;
      fill: none;
      stroke: currentColor;
      stroke-width: 2;
      stroke-linecap: round;
      stroke-linejoin: round;
    }
    .na-body {
      display: flex;
      flex-direction: column;
      gap: 0.2rem;
      flex: 1;
      min-width: 0;
      padding: 0;
      border: 0;
      background: none;
      color: inherit;
      font: inherit;
      text-align: left;
      cursor: pointer;
    }
    .na-body strong {
      font-size: 0.88rem;
      color: var(--color-text-strong);
    }
    .na-body span {
      font-size: 0.8rem;
      line-height: 1.4;
      color: var(--color-text-muted);
    }
    .na-body small {
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--color-accent);
    }
    .na-x {
      align-self: flex-start;
      display: inline-grid;
      place-items: center;
      width: 1.6rem;
      height: 1.6rem;
      border: 0;
      border-radius: 0.45rem;
      background: none;
      color: var(--color-text-subtle);
      cursor: pointer;
    }
    .na-x:hover {
      background: var(--color-surface-2);
    }
  `,
})
export class NotificacionAvisoComponent implements OnDestroy {
  protected readonly svc = inject(NotificacionesService);
  private timer: ReturnType<typeof setTimeout> | null = null;

  constructor() {
    // Se oculta solo a los pocos segundos; sigue disponible en la campana
    effect(() => {
      const a = this.svc.aviso();
      if (this.timer) clearTimeout(this.timer);
      if (a) this.timer = setTimeout(() => this.svc.aviso.set(null), DURACION_MS);
    });
  }

  ngOnDestroy(): void {
    if (this.timer) clearTimeout(this.timer);
  }
}
