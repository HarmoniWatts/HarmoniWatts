import { Component, computed, inject } from '@angular/core';
import { NotificacionItemComponent } from './notificacion-item.component';
import { NotificacionesService } from './notificaciones.service';

/** Tarjeta pequeña del dashboard con las últimas notificaciones (HAR-21). */
@Component({
  selector: 'app-ultimas-notificaciones',
  standalone: true,
  imports: [NotificacionItemComponent],
  template: `
    <section class="un">
      <header class="un-head">
        <h2>Últimas notificaciones</h2>
        @if (svc.items().length) {
          <button type="button" class="un-link" (click)="svc.abrirPanel()">Ver todas</button>
        }
      </header>
      @for (n of ultimas(); track n.id) {
        <app-notificacion-item [n]="n" [leida]="svc.esLeida(n.id)" [compacta]="true" (abrir)="abrir($event)" />
      } @empty {
        <p class="un-empty">{{ svc.loading() ? 'Buscando alertas…' : 'Todo en orden: no hay alertas por ahora.' }}</p>
      }
    </section>
  `,
  styles: `
    :host {
      display: block;
    }
    .un {
      border-radius: 1rem;
      border: 1px solid var(--color-border-strong);
      background: var(--color-surface-elev);
      box-shadow: var(--shadow-card);
      padding: 1.1rem 0.85rem 0.85rem;
      color: var(--color-text);
    }
    .un-head {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 0.5rem;
      padding: 0 0.4rem 0.35rem;
    }
    .un-head h2 {
      margin: 0;
      font-size: 1.05rem;
      font-weight: 600;
      color: var(--color-text-strong);
    }
    .un-link {
      padding: 0;
      border: 0;
      background: none;
      color: var(--color-accent);
      font: inherit;
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
    }
    .un-empty {
      margin: 0.4rem;
      font-size: 0.85rem;
      color: var(--color-text-subtle);
    }
  `,
})
export class UltimasNotificacionesComponent {
  protected readonly svc = inject(NotificacionesService);
  readonly ultimas = computed(() => this.svc.items().slice(0, 4));

  abrir(id: string): void {
    this.svc.marcarLeida(id);
    this.svc.abrirPanel();
  }
}
