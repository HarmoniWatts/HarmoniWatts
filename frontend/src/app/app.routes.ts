import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  {
    path: '',
    loadComponent: () => import('./features/layout/dash-shell.component').then((m) => m.DashShellComponent),
    canActivate: [authGuard],
    children: [
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./features/dashboard/dashboard.component').then((m) => m.DashboardComponent),
      },
      {
        path: 'cuenta',
        loadComponent: () =>
          import('./features/cuenta/cuenta-hub.component').then((m) => m.CuentaHubComponent),
      },
      {
        path: 'mi-vivienda',
        loadComponent: () =>
          import('./features/vivienda/mi-vivienda.component').then((m) => m.MiViviendaComponent),
      },
      {
        path: 'cuenta/electrodomesticos',
        loadComponent: () =>
          import('./features/electrodomesticos/electrodomesticos-page.component').then(
            (m) => m.ElectrodomesticosPageComponent,
          ),
      },
      {
        path: 'perfil/editar/datos',
        loadComponent: () =>
          import('./features/profile/perfil-datos.component').then((m) => m.PerfilDatosComponent),
      },
      {
        path: 'perfil/editar/contrasena',
        loadComponent: () =>
          import('./features/profile/perfil-contrasena.component').then((m) => m.PerfilContrasenaComponent),
      },
      {
        path: 'perfil/editar',
        loadComponent: () =>
          import('./features/profile/perfil-editar.component').then((m) => m.PerfilEditarComponent),
      },
    ],
  },
  {
    path: 'auth',
    loadChildren: () => import('./features/auth/auth.routes').then((m) => m.AUTH_ROUTES),
  },
  { path: '**', redirectTo: 'dashboard' },
];
