import { CommonModule } from '@angular/common';
import { Component, DestroyRef, inject, OnInit, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { finalize } from 'rxjs/operators';
import Keycloak from 'keycloak-js';
import { AccountService } from './account.service';

@Component({
  selector: 'app-perfil-datos',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './perfil-datos.component.html',
  styleUrl: './perfil-datos.component.css',
})
export class PerfilDatosComponent implements OnInit {
  private readonly account = inject(AccountService);
  private readonly keycloak = inject(Keycloak);
  private readonly destroyRef = inject(DestroyRef);

  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal(false);

  firstName = '';
  lastName = '';
  email = '';

  ngOnInit(): void {
    void this.keycloak
      .updateToken(60)
      .catch(() => undefined)
      .finally(() => {
        void this.keycloak
          .loadUserProfile()
          .then((p) => {
            this.firstName = p.firstName ?? '';
            this.lastName = p.lastName ?? '';
            this.email = p.email ?? '';
          })
          .catch(() => this.error.set('No se pudo cargar el perfil.'));
      });
  }

  guardar(): void {
    const fn = this.firstName.trim();
    const ln = this.lastName.trim();
    if (!fn || !ln) {
      this.error.set('Nombre y apellido son obligatorios.');
      return;
    }
    this.error.set(null);
    this.success.set(false);
    this.runWithFreshToken(() => {
      this.loading.set(true);
      this.account
        .updateProfile({
          firstName: fn,
          lastName: ln,
          email: this.email.trim() || undefined,
        })
        .pipe(
          takeUntilDestroyed(this.destroyRef),
          finalize(() => this.loading.set(false)),
        )
        .subscribe({
          next: () => {
            this.success.set(true);
            void this.keycloak.loadUserProfile().then((p) => {
              this.firstName = p.firstName ?? '';
              this.lastName = p.lastName ?? '';
              this.email = p.email ?? '';
            });
          },
          error: (err: { error?: { message?: string; detail?: string }; status?: number }) => {
            const raw = err?.error;
            const fromApi =
              typeof raw === 'object' && raw && 'message' in raw && typeof raw.message === 'string'
                ? raw.message
                : typeof raw === 'object' && raw && 'detail' in raw && typeof raw.detail === 'string'
                  ? raw.detail
                  : null;
            const msg =
              fromApi ??
              (err?.status === 503
                ? 'El servicio harmoni-register no está disponible o no puede hablar con Keycloak.'
                : 'No se pudo guardar los datos.');
            this.error.set(msg);
          },
        });
    });
  }

  private runWithFreshToken(run: () => void): void {
    if (!this.keycloak.authenticated) {
      run();
      return;
    }
    void this.keycloak
      .updateToken(60)
      .then(() => run())
      .catch(() => {
        void this.keycloak.login({
          redirectUri: `${window.location.origin}/perfil/editar/datos`,
        });
      });
  }
}
