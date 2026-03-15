import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../../environments/environment';
import { LogoComponent } from '../../../shared/components/logo';

@Component({
  selector: 'app-forgot-password',
  standalone: true,
  imports: [FormsModule, RouterLink, LogoComponent],
  templateUrl: './forgot-password.component.html',
  styleUrls: ['./forgot-password.component.css'],
})
export class ForgotPasswordComponent {
  loading = false;
  email = '';
  errorMessage = '';
  successMessage = '';
  private readonly http = inject(HttpClient);

  get forgotPasswordApiUrl(): string | undefined {
    return (environment as { forgotPasswordApiUrl?: string }).forgotPasswordApiUrl;
  }

  submit(): void {
    this.errorMessage = '';
    this.successMessage = '';
    const apiUrl = this.forgotPasswordApiUrl;
    const email = this.email?.trim();
    if (!email) {
      this.errorMessage = 'Indica tu correo electrónico.';
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      this.errorMessage = 'El correo no es válido.';
      return;
    }
    if (!apiUrl) {
      this.errorMessage =
        'No hay backend configurado para restablecer contraseña. Configura forgotPasswordApiUrl en environment.';
      return;
    }
    this.loading = true;
    this.http.post<{ success?: boolean }>(apiUrl, { email }).subscribe({
      next: () => {
        this.loading = false;
        this.successMessage =
          'Si existe una cuenta con ese correo, recibirás un enlace para restablecer tu contraseña. Revisa tu bandeja de entrada y la carpeta de spam.';
      },
      error: (err: { status?: number; message?: string }) => {
        this.loading = false;
        if (err?.status === 0 || err?.message?.toLowerCase().includes('fetch failed')) {
          this.errorMessage =
            'No se pudo conectar con el servidor. Comprueba que harmoni-register esté en marcha (puerto 8081).';
        } else {
          this.successMessage =
            'Si existe una cuenta con ese correo, recibirás un enlace para restablecer tu contraseña.';
        }
      },
    });
  }
}
