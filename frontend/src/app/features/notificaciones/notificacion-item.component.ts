import { Component, computed, input, output } from '@angular/core';
import type { Notificacion } from './notificaciones.service';

const SEVERIDAD: Record<string, { label: string; clase: string }> = {
  HIGH: { label: 'Alta', clase: 'ni-alta' },
  MEDIUM: { label: 'Media', clase: 'ni-media' },
  LOW: { label: 'Baja', clase: 'ni-baja' },
};

/** «hace 5 min», «hace 3 h», «ayer 18:00», «19 nov 18:00» desde una hora local. */
export function cuando(fecha: string, ahora = new Date()): string {
  const [d, t = '00:00'] = fecha.split('T');
  const [a, m, dd] = d.split('-').map(Number);
  const [h, mi] = t.split(':').map(Number);
  const f = new Date(a, m - 1, dd, h, mi);
  const min = Math.round((ahora.getTime() - f.getTime()) / 60000);
  const hhmm = `${String(h).padStart(2, '0')}:${String(mi).padStart(2, '0')}`;
  if (min < 0) return `hoy ${hhmm}`;
  if (min < 1) return 'ahora';
  if (min < 60) return `hace ${min} min`;
  if (min < 12 * 60) return `hace ${Math.round(min / 60)} h`;
  const ayer = new Date(ahora.getFullYear(), ahora.getMonth(), ahora.getDate() - 1);
  if (f.toDateString() === ahora.toDateString()) return `hoy ${hhmm}`;
  if (f.toDateString() === ayer.toDateString()) return `ayer ${hhmm}`;
  return `${f.toLocaleDateString('es-CO', { day: 'numeric', month: 'short' }).replace('.', '')} ${hhmm}`;
}

/** Una notificación: ícono por tipo, nivel de severidad, título, mensaje y hora. */
@Component({
  selector: 'app-notificacion-item',
  standalone: true,
  template: `
    <article class="ni" [class.ni-leida]="leida()" [class.ni-compacta]="compacta()" (click)="abrir.emit(n().id)">
      <span class="ni-ic {{ sev()?.clase ?? 'ni-ia' }}" aria-hidden="true">
        @switch (icono()) {
          @case ('franja') {
            <svg viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" /></svg>
          }
          @case ('consumo') {
            <svg viewBox="0 0 24 24"><polyline points="3 17 9 11 13 15 21 7" /><polyline points="15 7 21 7 21 13" /></svg>
          }
          @default {
            <svg viewBox="0 0 24 24"><path d="M9 18h6" /><path d="M10 22h4" /><path d="M12 2a7 7 0 0 0-4 13v3h8v-3a7 7 0 0 0-4-13z" /></svg>
          }
        }
      </span>
      <div class="ni-body">
        <div class="ni-top">
          <strong class="ni-title">{{ n().titulo }}</strong>
          @if (!leida()) {
            <i class="ni-dot" aria-label="No leída"></i>
          }
        </div>
        @if (!compacta()) {
          <p class="ni-msg">{{ n().mensaje }}</p>
        }
        <div class="ni-meta">
          @if (sev(); as s) {
            <span class="ni-pill {{ s.clase }}">Severidad {{ s.label.toLowerCase() }}</span>
          } @else {
            <span class="ni-pill ni-ia">Recomendación IA</span>
          }
          <span class="ni-time">{{ hora() }}</span>
        </div>
      </div>
    </article>
  `,
  styles: `
    .ni {
      display: flex;
      gap: 0.7rem;
      padding: 0.7rem 0.75rem;
      border-radius: 0.75rem;
      cursor: pointer;
      transition: background 0.15s;
    }
    .ni:hover {
      background: var(--color-surface-2);
    }
    .ni-leida {
      opacity: 0.72;
    }
    .ni-compacta {
      padding: 0.5rem 0.55rem;
    }
    .ni-ic {
      display: inline-grid;
      place-items: center;
      flex-shrink: 0;
      width: 2rem;
      height: 2rem;
      border-radius: 0.6rem;
    }
    .ni-ic svg {
      width: 1rem;
      height: 1rem;
      fill: none;
      stroke: currentColor;
      stroke-width: 2;
      stroke-linecap: round;
      stroke-linejoin: round;
    }
    .ni-body {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
      min-width: 0;
      flex: 1;
    }
    .ni-top {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 0.5rem;
    }
    .ni-title {
      font-size: 0.85rem;
      line-height: 1.3;
      color: var(--color-text-strong);
    }
    .ni-dot {
      flex-shrink: 0;
      width: 0.5rem;
      height: 0.5rem;
      margin-top: 0.3rem;
      border-radius: 50%;
      background: var(--color-accent);
    }
    .ni-msg {
      margin: 0;
      font-size: 0.8rem;
      line-height: 1.4;
      color: var(--color-text-muted);
    }
    .ni-meta {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.3rem 0.6rem;
    }
    .ni-pill {
      padding: 0.05rem 0.45rem;
      border-radius: 999px;
      border: 1px solid transparent;
      font-size: 0.68rem;
      font-weight: 600;
      white-space: nowrap;
    }
    .ni-time {
      font-size: 0.72rem;
      color: var(--color-text-subtle);
    }
    .ni-alta {
      color: var(--color-danger-text);
      background: var(--color-danger-soft);
      border-color: color-mix(in srgb, var(--color-danger) 35%, transparent);
    }
    .ni-media {
      color: var(--color-warning-text);
      background: var(--color-warning-soft);
      border-color: color-mix(in srgb, var(--color-warning) 35%, transparent);
    }
    .ni-baja {
      color: var(--color-accent);
      background: var(--color-accent-soft);
      border-color: var(--color-accent-border);
    }
    .ni-ia {
      color: #a78bfa;
      background: color-mix(in srgb, #a78bfa 14%, transparent);
      border-color: color-mix(in srgb, #a78bfa 35%, transparent);
    }
  `,
})
export class NotificacionItemComponent {
  readonly n = input.required<Notificacion>();
  readonly leida = input(false);
  readonly compacta = input(false);
  readonly abrir = output<string>();

  readonly sev = computed(() => (this.n().severidad ? SEVERIDAD[this.n().severidad!] : null));
  readonly icono = computed(() => {
    const t = this.n().tipo;
    return t.startsWith('TARIFF') ? 'franja' : t.startsWith('CONSUMPTION') ? 'consumo' : 'ia';
  });
  readonly hora = computed(() => cuando(this.n().fecha));
}
