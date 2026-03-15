import { Component, inject } from '@angular/core';
import Keycloak from 'keycloak-js';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [],
  template: `
    <div class="dashboard">
      <header>
        <h1>HarmoniWatts</h1>
        <button type="button" class="btn btn-secondary" (click)="logout()">Cerrar sesión</button>
      </header>
      <main>
        <p>Bienvenido. Esta es un área protegida; solo usuarios autenticados pueden verla.</p>
      </main>
    </div>
  `,
  styles: [
    `
      .dashboard { padding: 1.5rem; max-width: 800px; margin: 0 auto; }
      header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
      header h1 { margin: 0; font-size: 1.5rem; }
    `,
  ],
})
export class DashboardComponent {
  private readonly keycloak = inject(Keycloak);

  logout(): void {
    this.keycloak.logout({ redirectUri: window.location.origin + '/auth/login' });
  }
}
