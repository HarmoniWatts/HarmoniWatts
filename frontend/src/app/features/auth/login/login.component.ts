import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import Keycloak from 'keycloak-js';
import { applyKeycloakResourceOwnerPasswordTokens } from '../../../core/auth/keycloak-direct-grant.util';
import { environment } from '../../../../environments/environment';
import { LogoComponent } from '../../../shared/components/logo';
import { ThemeToggleComponent } from '../../../shared/components/theme-toggle';

const { url, realm, clientId } = environment.keycloak;
const TOKEN_URL = `${url}/realms/${realm}/protocol/openid-connect/token`;

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule, RouterLink, LogoComponent, ThemeToggleComponent],
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
  private readonly route = inject(ActivatedRoute);

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
          applyKeycloakResourceOwnerPasswordTokens(
            this.keycloak,
            res.access_token,
            res.refresh_token,
            res.id_token,
          );
          this.loading = false;
          const returnUrl = this.route.snapshot.queryParamMap.get('returnUrl') || '/dashboard';
          void this.router.navigateByUrl(returnUrl);
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
