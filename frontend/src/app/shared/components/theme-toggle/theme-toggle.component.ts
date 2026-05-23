import { ChangeDetectionStrategy, Component, computed, inject, input } from '@angular/core';
import { ThemeService } from '../../../core/theme/theme.service';

/**
 * Botón accesible para alternar entre tema oscuro y claro.
 * No conoce dónde se ubica: depende del `ThemeService` (puerto).
 *
 * Variantes visuales se controlan con la clase aplicada desde el contenedor:
 *   - `.theme-toggle--icon` (default): solo icono, ideal para sidebar.
 *   - `.theme-toggle--floating`: pill flotante (ideal para pantallas de auth).
 */
@Component({
  selector: 'app-theme-toggle',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    /* Cuando es flotante, el botón se posiciona `fixed`. Sacamos el host
       del flujo (display: contents vía clase) para que no ocupe celda en
       contenedores grid/flex. */
    '[class.theme-toggle-host--floating]': 'floating()',
  },
  template: `
    <button
      type="button"
      class="theme-toggle"
      [class.theme-toggle--floating]="floating()"
      [attr.aria-label]="ariaLabel()"
      [attr.title]="ariaLabel()"
      [attr.aria-pressed]="isLight()"
      (click)="onToggle()"
    >
      @if (isLight()) {
        <!-- Icono luna (estamos en claro: el botón llevará a oscuro) -->
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
        </svg>
      } @else {
        <!-- Icono sol (estamos en oscuro: el botón llevará a claro) -->
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <circle cx="12" cy="12" r="4" />
          <path
            d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"
          />
        </svg>
      }
      @if (showLabel()) {
        <span class="theme-toggle__label">{{ isLight() ? 'Modo oscuro' : 'Modo claro' }}</span>
      }
    </button>
  `,
  styleUrl: './theme-toggle.component.css',
})
export class ThemeToggleComponent {
  /** Si `true`, se muestra etiqueta de texto junto al icono. */
  readonly showLabel = input<boolean>(false);
  /** Variante flotante para pantallas sin chrome de app (auth). */
  readonly floating = input<boolean>(false);

  private readonly themeSvc = inject(ThemeService);

  readonly isLight = computed(() => this.themeSvc.theme() === 'light');
  readonly ariaLabel = computed(() =>
    this.isLight() ? 'Cambiar a modo oscuro' : 'Cambiar a modo claro',
  );

  onToggle(): void {
    this.themeSvc.toggle();
  }
}
