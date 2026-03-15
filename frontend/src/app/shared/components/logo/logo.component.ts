import { Component, input } from '@angular/core';

/**
 * Logo oficial de HarmoniWatts (rayo en círculo con gradiente y contorno por capas).
 * Reutilizable en login, header, dashboard, etc.
 *
 * Uso:
 *   <app-logo />
 *   <app-logo [size]="40" />
 *   <app-logo [size]="32" [animated]="false" />
 */
@Component({
  selector: 'app-logo',
  standalone: true,
  imports: [],
  templateUrl: './logo.component.html',
  styleUrl: './logo.component.css',
})
export class LogoComponent {
  /** Tamaño en píxeles (ancho y alto). Por defecto 56. */
  size = input<number>(56);
  /** Si true, aplica la animación de brillo pulsante. Por defecto false. */
  animated = input<boolean>(false);
  /** Id único para el gradiente (evita conflictos si hay varios logos en la misma página). */
  readonly gradId = 'hw-logo-grad-' + Math.random().toString(36).slice(2, 9);
}
