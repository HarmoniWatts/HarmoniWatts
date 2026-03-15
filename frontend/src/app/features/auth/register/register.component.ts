import { Component, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import Keycloak from 'keycloak-js';
import { environment } from '../../../../environments/environment';
import { LogoComponent } from '../../../shared/components/logo';

export type PasswordStrength = 'weak' | 'medium' | 'strong' | 'very-strong' | '';

function getPasswordStrength(pwd: string): PasswordStrength {
  if (!pwd) return '';
  let score = 0;
  if (pwd.length >= 8) score++;
  if (pwd.length >= 12) score++;
  if (/[a-z]/.test(pwd) && /[A-Z]/.test(pwd)) score++;
  if (/\d/.test(pwd)) score++;
  if (/[^a-zA-Z0-9]/.test(pwd)) score++;
  if (score <= 1) return 'weak';
  if (score <= 2) return 'medium';
  if (score <= 4) return 'strong';
  return 'very-strong';
}

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [FormsModule, RouterLink, LogoComponent],
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.css'],
})
export class RegisterComponent {
  firstName = '';
  lastName = '';
  email = '';
  city = '';
  password = '';
  passwordConfirm = '';
  acceptTerms = false;
  loading = false;
  showPassword = false;
  showPasswordConfirm = false;
  errorMessage = '';
  successMessage = '';

  passwordStrength: PasswordStrength = '';
  readonly cities = [
    'Bogotá',
    'Medellín',
    'Cali',
    'Barranquilla',
    'Cartagena',
    'Cúcuta',
    'Bucaramanga',
    'Pereira',
    'Santa Marta',
    'Otra',
  ];

  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly keycloak = inject(Keycloak);

  get registrationApiUrl(): string | undefined {
    const url = (environment as { registrationApiUrl?: string }).registrationApiUrl;
    return url && url.trim() ? url : undefined;
  }

  onPasswordInput(): void {
    this.passwordStrength = getPasswordStrength(this.password);
  }

  passwordsMatch(): boolean {
    return this.password === this.passwordConfirm && this.passwordConfirm.length > 0;
  }

  submit(): void {
    this.errorMessage = '';
    this.successMessage = '';

    if (!this.firstName?.trim() || !this.lastName?.trim()) {
      this.errorMessage = 'Nombre y apellido son obligatorios.';
      return;
    }
    if (!this.email?.trim()) {
      this.errorMessage = 'El correo electrónico es obligatorio.';
      return;
    }
    const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRe.test(this.email.trim())) {
      this.errorMessage = 'Introduce un correo electrónico válido.';
      return;
    }
    if (this.password.length < 8) {
      this.errorMessage = 'La contraseña debe tener al menos 8 caracteres.';
      return;
    }
    if (this.password !== this.passwordConfirm) {
      this.errorMessage = 'Las contraseñas no coinciden.';
      return;
    }
    if (!this.acceptTerms) {
      this.errorMessage = 'Debes aceptar los Términos y Condiciones y la Política de Privacidad.';
      return;
    }

    this.loading = true;
    const payload = {
      firstName: this.firstName.trim(),
      lastName: this.lastName.trim(),
      email: this.email.trim(),
      username: this.email.trim(),
      city: this.city || undefined,
      password: this.password,
    };

    const apiUrl = this.registrationApiUrl;
    if (!apiUrl) {
      this.loading = false;
      this.errorMessage =
        'El registro desde este formulario requiere un backend configurado. Configura registrationApiUrl en environment (ver docs/REGISTER-API.md).';
      return;
    }

    this.http.post(apiUrl, payload).subscribe({
      next: () => this.onRegisterSuccess(),
      error: (err) => this.onRegisterError(err),
    });
  }

  private onRegisterSuccess(): void {
    this.loading = false;
    this.successMessage = 'Cuenta creada. Revisa tu correo para verificar tu email.';
    setTimeout(() => this.router.navigate(['/auth/login']), 3000);
  }

  private onRegisterError(err: unknown): void {
    this.loading = false;
    const e = err as { error?: { message?: string } | string; status?: number; message?: string };
    const status = e?.status;
    if (status === 0 || e?.message?.toLowerCase().includes('fetch failed') || e?.message?.toLowerCase().includes('failed to fetch')) {
      this.errorMessage =
        'No se pudo conectar con el servidor de registro. Comprueba que harmoni-register esté en marcha (puerto 8081). Si usas Docker: docker compose up -d.';
      return;
    }
    const msg = typeof e?.error === 'object' ? (e.error as { message?: string })?.message : e?.error;
    this.errorMessage = (typeof msg === 'string' ? msg : 'Error al crear la cuenta.') || 'Error al crear la cuenta.';
  }

  /** Redirige a la página de registro de Keycloak (opcional, si no hay backend). */
  registerWithKeycloak(): void {
    this.keycloak.register({
      redirectUri: window.location.origin + '/auth/login',
    });
  }
}
