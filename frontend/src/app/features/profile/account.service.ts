import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface ProfileUpdatePayload {
  firstName: string;
  lastName: string;
  /** Si se omite o va vacío, el backend no cambia el email en Keycloak */
  email?: string;
}

@Injectable({ providedIn: 'root' })
export class AccountService {
  private readonly http = inject(HttpClient);

  /** harmoni-register: perfil y contraseña en Keycloak (no la API de viviendas). */
  private baseUrl(): string {
    const root = (
      environment.harmoniRegisterBaseUrl ??
      environment.apiBaseUrl ??
      ''
    ).replace(/\/$/, '');
    return `${root}/api/auth`;
  }

  updateProfile(body: ProfileUpdatePayload): Observable<void> {
    return this.http.put<void>(`${this.baseUrl()}/profile`, body);
  }

  changePassword(currentPassword: string, newPassword: string): Observable<void> {
    return this.http.put<void>(`${this.baseUrl()}/password`, {
      currentPassword,
      newPassword,
    });
  }
}
