import { CommonModule } from '@angular/common';
import { Component, DestroyRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs/operators';
import Keycloak from 'keycloak-js';

@Component({
  selector: 'app-dash-shell',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './dash-shell.component.html',
  styleUrl: './dash-shell.component.css',
})
export class DashShellComponent {
  private readonly keycloak = inject(Keycloak);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  readonly userInitials = signal('HW');
  /** Resalta «Cuenta» cuando estás en el hub o en perfil / vivienda. */
  readonly cuentaSectionActive = signal(false);

  constructor() {
    const updateCuentaActive = (): void => {
      const path = this.router.url.split('?')[0];
      this.cuentaSectionActive.set(
        path === '/cuenta' || path.startsWith('/perfil') || path === '/mi-vivienda',
      );
    };
    updateCuentaActive();
    this.router.events
      .pipe(
        filter((e): e is NavigationEnd => e instanceof NavigationEnd),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe(() => {
        updateCuentaActive();
        void this.refreshKeycloakToken();
      });

    void this.refreshKeycloakToken();

    const onVisibility = (): void => {
      if (document.visibilityState === 'visible') {
        void this.refreshKeycloakToken();
      }
    };
    document.addEventListener('visibilitychange', onVisibility);
    this.destroyRef.onDestroy(() => document.removeEventListener('visibilitychange', onVisibility));

    void this.keycloak
      .loadUserProfile()
      .then((p) => {
        const fn = (p.firstName ?? '').trim();
        const ln = (p.lastName ?? '').trim();
        let initials = ((fn[0] ?? '') + (ln[0] ?? '')).trim();
        if (!initials && p.username) {
          initials = p.username.substring(0, 2);
        }
        if (initials) {
          this.userInitials.set(initials.toUpperCase());
        }
      })
      .catch(() => undefined);
  }

  logout(): void {
    this.keycloak.logout({ redirectUri: window.location.origin + '/auth/login' });
  }

  /**
   * Renueva el access token si hace falta (vuelta desde Keycloak, cambio de ruta, pestaña activa).
   * Min 60 s de validez restante para alinear con llamadas al backend.
   */
  private refreshKeycloakToken(): void {
    if (!this.keycloak.authenticated) {
      return;
    }
    void this.keycloak.updateToken(60).catch(() => undefined);
  }
}
