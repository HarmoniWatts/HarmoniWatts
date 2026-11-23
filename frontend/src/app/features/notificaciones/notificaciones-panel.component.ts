import { Component, computed, HostListener, inject } from '@angular/core';
import { NotificacionItemComponent } from './notificacion-item.component';
import { NotificacionesService } from './notificaciones.service';

/** Panel de la campana: alertas (HAR-21) y recomendaciones IA de la vivienda activa. */
@Component({
  selector: 'app-notificaciones-panel',
  standalone: true,
  imports: [NotificacionItemComponent],
  template: `
    @if (svc.panelAbierto()) {
      <div class="np-backdrop" (click)="svc.panelAbierto.set(false)"></div>
      <section class="np" role="dialog" aria-label="Notificaciones">
        <header class="np-head">
          <h2>Notificaciones</h2>
          <div class="np-actions">
            @if (svc.noLeidas()) {
              <button type="button" class="np-link" (click)="svc.marcarTodasLeidas()">Marcar todo como leído</button>
            }
            <button type="button" class="np-x" (click)="svc.panelAbierto.set(false)" aria-label="Cerrar">
              <svg viewBox="0 0 24 24"><line x1="6" y1="6" x2="18" y2="18" /><line x1="18" y1="6" x2="6" y2="18" /></svg>
            </button>
          </div>
        </header>
        <div class="np-list">
          @if (alertas().length) {
            <h3 class="np-group">Alertas</h3>
            @for (n of alertas(); track n.id) {
              <app-notificacion-item [n]="n" [leida]="svc.esLeida(n.id)" (abrir)="svc.marcarLeida($event)" />
            }
          }
          @if (ia().length) {
            <h3 class="np-group">Recomendaciones IA</h3>
            @for (n of ia(); track n.id) {
              <app-notificacion-item [n]="n" [leida]="svc.esLeida(n.id)" (abrir)="svc.marcarLeida($event)" />
            }
          }
          @if (!svc.items().length) {
            <p class="np-empty">
              @if (svc.loading()) {
                Buscando alertas…
              } @else if (svc.error()) {
                {{ svc.error() }}
              } @else {
                Todo en orden: no hay alertas por ahora.
              }
            </p>
          }
        </div>
        <footer class="np-foot">
          Se revisan cada 5 minutos: franja de precio alto y consumo por encima de lo habitual.
        </footer>
      </section>
    }
  `,
  styles: `
    .np-backdrop {
      position: fixed;
      inset: 0;
      z-index: 60;
    }
    .np {
      position: fixed;
      top: 0.75rem;
      left: calc(72px + 0.75rem);
      z-index: 61;
      display: flex;
      flex-direction: column;
      width: min(24rem, calc(100vw - 72px - 1.5rem));
      max-height: calc(100vh - 1.5rem);
      border-radius: 1rem;
      border: 1px solid var(--color-border-strong);
      background: var(--color-bg-solid);
      box-shadow: 0 18px 48px rgba(0, 0, 0, 0.35);
      color: var(--color-text);
    }
    .np-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.5rem;
      padding: 0.9rem 1rem 0.6rem;
      border-bottom: 1px solid var(--color-border);
    }
    .np-head h2 {
      margin: 0;
      font-size: 1rem;
      color: var(--color-text-strong);
    }
    .np-actions {
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }
    .np-link {
      padding: 0;
      border: 0;
      background: none;
      color: var(--color-accent);
      font: inherit;
      font-size: 0.78rem;
      font-weight: 600;
      cursor: pointer;
    }
    .np-x {
      display: inline-grid;
      place-items: center;
      width: 1.8rem;
      height: 1.8rem;
      border-radius: 0.5rem;
      border: 1px solid var(--color-border-input);
      background: var(--color-surface-2);
      color: var(--color-text-muted);
      cursor: pointer;
    }
    .np-x svg {
      width: 0.85rem;
      height: 0.85rem;
      fill: none;
      stroke: currentColor;
      stroke-width: 2.25;
      stroke-linecap: round;
    }
    .np-list {
      overflow-y: auto;
      padding: 0.35rem 0.4rem;
    }
    .np-group {
      margin: 0.5rem 0.4rem 0.2rem;
      font-size: 0.7rem;
      font-weight: 600;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      color: var(--color-text-subtle);
    }
    .np-empty {
      margin: 1.25rem 0.75rem;
      font-size: 0.85rem;
      text-align: center;
      color: var(--color-text-muted);
    }
    .np-foot {
      padding: 0.6rem 1rem 0.8rem;
      border-top: 1px solid var(--color-border);
      font-size: 0.72rem;
      color: var(--color-text-subtle);
    }
    @media (max-width: 600px) {
      .np {
        left: 0.5rem;
        right: 0.5rem;
        width: auto;
      }
    }
  `,
})
export class NotificacionesPanelComponent {
  protected readonly svc = inject(NotificacionesService);

  readonly alertas = computed(() => this.svc.items().filter((n) => n.origen === 'ALERTA'));
  readonly ia = computed(() => this.svc.items().filter((n) => n.origen === 'IA'));

  @HostListener('document:keydown.escape')
  cerrar(): void {
    this.svc.panelAbierto.set(false);
  }
}
