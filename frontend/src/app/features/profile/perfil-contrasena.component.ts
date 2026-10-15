import { CommonModule } from '@angular/common';
import { Component, DestroyRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { finalize } from 'rxjs/operators';
import Keycloak from 'keycloak-js';
import { AccountService } from './account.service';

@Component({
  selector: 'app-perfil-contrasena',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './perfil-contrasena.component.html',
  styleUrl: './perfil-contrasena.component.css',
})
export class PerfilContrasenaComponent {
  private readonly account = inject(AccountService);
  private readonly keycloak = inject(Keycloak);
  private readonly destroyRef = inject(DestroyRef);

  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal(false);

  currentPassword = '';
  newPassword = '';
  confirmPassword = '';

  guardar(): void {
    this.error.set(null);
    this.success.set(false);
    if (this.newPassword.length < 8) {
      this.error.set('La nueva contraseña debe tener al menos 8 caracteres.');
      return;
    }
    if (this.newPassword !== this.confirmPassword) {
      this.error.set('La confirmación no coincide con la nueva contraseña.');
      return;
    }
    this.runWithFreshToken(() => {
      this.loading.set(true);
      this.account
        .changePassword(this.currentPassword, this.newPassword)
        .pipe(
          takeUntilDestroyed(this.destroyRef),
          finalize(() => this.loading.set(false)),
        )
        .subscribe({
          next: () => {
            this.success.set(true);
            this.currentPassword = '';
            this.newPassword = '';
            this.confirmPassword = '';
          },
          error: (err: { error?: { message?: string; detail?: string }; status?: number }) => {
            const raw = err?.error;
            const msg =
              (typeof raw === 'object' && raw && 'message' in raw && typeof raw.message === 'string'
                ? raw.message
                : null) ??
              (typeof raw === 'object' && raw && 'detail' in raw && typeof raw.detail === 'string'
                ? raw.detail
                : null);
            if (err?.status === 401) {
              this.error.set('La contraseña actual no es correcta.');
            } else if (err?.status === 503) {
              this.error.set('El servicio harmoni-register no está disponible o no puede hablar con Keycloak.');
            } else {
              this.error.set(msg ?? 'No se pudo cambiar la contraseña.');
            }
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
          redirectUri: `${window.location.origin}/perfil/editar/contrasena`,
        });
      });
  }
}
