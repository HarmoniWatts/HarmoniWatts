import { CommonModule } from '@angular/common';
import { Component, computed, DestroyRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed, toSignal } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { of } from 'rxjs';
import { catchError, filter } from 'rxjs/operators';
import Keycloak from 'keycloak-js';
import { ThemeToggleComponent } from '../../shared/components/theme-toggle';
import {
  clearStoredKeycloakTokens,
  persistKeycloakTokens,
} from '../../core/auth/keycloak-direct-grant.util';
import { TarifasService } from '../tarifas/tarifas.service';
import { ViviendaContextService } from '../vivienda/vivienda-context.service';

@Component({
  selector: 'app-dash-shell',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive, ThemeToggleComponent],
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

  private readonly viviendaCtx = inject(ViviendaContextService);
  private readonly ciudades = toSignal(
    inject(TarifasService)
      .listCiudades()
      .pipe(catchError(() => of([]))),
    { initialValue: [] },
  );
  /** Municipio de la vivienda seleccionada (dashboard / tarifas). */
  readonly ciudadActiva = computed(() => {
    const u = this.viviendaCtx.ubicacion();
    const c = u && this.ciudades().find((x) => x.id_zona === u.idZona && x.cod_mercado === u.codMercado);
    return c?.municipio ?? 'Sin ciudad';
  });

  constructor() {
    const updateCuentaActive = (): void => {
      const path = this.router.url.split('?')[0];
      this.cuentaSectionActive.set(
        path.startsWith('/cuenta') ||
          path.startsWith('/perfil') ||
          path === '/mi-vivienda',
      );
    };
    updateCuentaActive();
    this.viviendaCtx.load().subscribe();
    this.router.events
      .pipe(
        filter((e): e is NavigationEnd => e instanceof NavigationEnd),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe(() => {
        updateCuentaActive();
        void this.refreshKeycloakToken();
      });

    /* Mantén sessionStorage sincronizado tras cada refresh exitoso del token,
       para que F5 use siempre el último access/refresh válido. */
    const previousOnRefresh = this.keycloak.onAuthRefreshSuccess;
    this.keycloak.onAuthRefreshSuccess = () => {
      if (this.keycloak.token && this.keycloak.refreshToken) {
        persistKeycloakTokens({
          access_token: this.keycloak.token,
          refresh_token: this.keycloak.refreshToken,
          id_token: this.keycloak.idToken ?? undefined,
        });
      }
      previousOnRefresh?.();
    };

    const previousOnLogout = this.keycloak.onAuthLogout;
    this.keycloak.onAuthLogout = () => {
      clearStoredKeycloakTokens();
      previousOnLogout?.();
    };

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

  /**
   * Cierre de sesión: invalida la sesión en Keycloak y vuelve al login.
   * Pide confirmación al usuario para evitar cierres accidentales.
   */
  logout(): void {
    const confirmed =
      typeof window === 'undefined'
        ? true
        : window.confirm('¿Cerrar tu sesión en HarmoniWatts?');
    if (!confirmed) {
      return;
    }
    clearStoredKeycloakTokens();
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
