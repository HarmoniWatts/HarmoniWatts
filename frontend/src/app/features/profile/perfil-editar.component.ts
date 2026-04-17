import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import Keycloak from 'keycloak-js';

@Component({
  selector: 'app-perfil-editar',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './perfil-editar.component.html',
  styleUrl: './perfil-editar.component.css',
})
export class PerfilEditarComponent {
  private readonly keycloak = inject(Keycloak);

  readonly profileLoading = signal(true);
  readonly email = signal<string | undefined>(undefined);
  readonly nombreCompleto = signal<string | undefined>(undefined);
  readonly username = signal<string | undefined>(undefined);

  constructor() {
    void this.keycloak
      .loadUserProfile()
      .then((p) => {
        this.email.set(p.email);
        const fn = [p.firstName, p.lastName].filter(Boolean).join(' ').trim();
        this.nombreCompleto.set(fn || undefined);
        this.username.set(p.username);
      })
      .catch(() => undefined)
      .finally(() => this.profileLoading.set(false));
  }

  /**
   * URL a la que Keycloak debe volver tras el flujo (evita perder el contexto de la SPA y fuerza nuevo intercambio de tokens).
   */
  private redirectTrasAccionKeycloak(): string {
    return `${window.location.origin}/perfil/editar`;
  }

  /** Flujo OIDC de Keycloak para actualizar datos de cuenta (nombre, apellidos, etc.). */
  editarInformacionPersonal(): void {
    void this.keycloak.login({
      action: 'UPDATE_PROFILE',
      redirectUri: this.redirectTrasAccionKeycloak(),
    });
  }

  /** Flujo dedicado de Keycloak para cambiar contraseña. */
  cambiarContrasena(): void {
    void this.keycloak.login({
      action: 'UPDATE_PASSWORD',
      redirectUri: this.redirectTrasAccionKeycloak(),
    });
  }
}
