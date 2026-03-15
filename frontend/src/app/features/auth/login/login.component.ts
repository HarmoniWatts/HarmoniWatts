import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import Keycloak from 'keycloak-js';
import { environment } from '../../../../environments/environment';
import { LogoComponent } from '../../../shared/components/logo';

const { url, realm, clientId } = environment.keycloak;
const TOKEN_URL = `${url}/realms/${realm}/protocol/openid-connect/token`;

function parseJwtPayload(token: string): Record<string, unknown> {
  try {
    const base64Url = token.split('.')[1];
    if (!base64Url) return {};
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    return JSON.parse(atob(base64)) as Record<string, unknown>;
  } catch {
    return {};
  }
}

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule, RouterLink, LogoComponent],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css'],
})
export class LoginComponent {
  loading = false;
  showPassword = false;
  email = '';
  password = '';
  errorMessage = '';
  private readonly keycloak = inject(Keycloak);
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  login(): void {
    this.errorMessage = '';
    const username = this.email?.trim();
    const pwd = this.password;
    if (!username || !pwd) {
      this.errorMessage = 'Indica correo y contraseña.';
      return;
    }
    this.loading = true;
    const body = new URLSearchParams({
      grant_type: 'password',
      client_id: clientId,
      username,
      password: pwd,
    });
    this.http
      .post<{ access_token: string; refresh_token: string; id_token?: string; expires_in?: number }>(
        TOKEN_URL,
        body.toString(),
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
      )
      .subscribe({
        next: (res) => {
          const k = this.keycloak as unknown as Record<string, unknown>;
          k['token'] = res.access_token;
          k['refreshToken'] = res.refresh_token;
          k['idToken'] = res.id_token ?? '';
          k['authenticated'] = true;
          k['tokenParsed'] = parseJwtPayload(res.access_token);
          if (res.id_token) k['idTokenParsed'] = parseJwtPayload(res.id_token);
          const parsed = k['tokenParsed'] as { sub?: string };
          if (parsed?.sub) k['subject'] = parsed.sub;
          this.router.navigate(['/dashboard']);
        },
        error: (err: { error?: { error_description?: string }; message?: string; status?: number }) => {
          this.loading = false;
          const msg = err?.error?.error_description ?? err?.message ?? 'Error al iniciar sesión.';
          if (err?.status === 401) {
            this.errorMessage = 'Correo o contraseña incorrectos.';
          } else {
            this.errorMessage = typeof msg === 'string' ? msg : 'Error al iniciar sesión.';
          }
        },
      });
  }

  loginWithGoogle(): void {
    this.loading = true;
    this.keycloak.login({
      idpHint: 'google',
      redirectUri: window.location.origin + '/dashboard',
    });
  }

}
