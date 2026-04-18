import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import Keycloak from 'keycloak-js';

@Component({
  selector: 'app-perfil-editar',
  standalone: true,
  imports: [CommonModule, RouterLink],
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

}
