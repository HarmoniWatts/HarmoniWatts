import { CommonModule } from '@angular/common';
import { Component, DestroyRef, inject, OnInit, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { finalize } from 'rxjs/operators';
import Keycloak from 'keycloak-js';
import type { ViviendaDto } from './vivienda.service';
import { ViviendaService } from './vivienda.service';

@Component({
  selector: 'app-mi-vivienda',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './mi-vivienda.component.html',
  styleUrl: './mi-vivienda.component.css',
})
export class MiViviendaComponent implements OnInit {
  private readonly api = inject(ViviendaService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly keycloak = inject(Keycloak);

  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly items = signal<ViviendaDto[]>([]);

  readonly tipos = ['Casa', 'Apartamento', 'Piso', 'Otro'] as const;
  readonly estratos = [1, 2, 3, 4, 5, 6] as const;

  /** Alta */
  tipoNuevo = 'Casa';
  habitantesNuevo: number | null = 3;
  estratoNuevo: number | null = 3;
  ubicacionNueva = '';

  /** Edición */
  editId: number | null = null;
  tipoEdit = 'Casa';
  habitantesEdit: number | null = 3;
  estratoEdit: number | null = 3;
  ubicacionEdit = '';
  zonaEdit = '';

  ngOnInit(): void {
    this.reload();
  }

  private redirectMiVivienda(): string {
    return `${window.location.origin}/mi-vivienda`;
  }

  /** Renueva el token antes de llamar al backend (evita 401 tras volver de Keycloak). */
  private runWithFreshToken(run: () => void): void {
    if (!this.keycloak.authenticated) {
      run();
      return;
    }
    void this.keycloak
      .updateToken(60)
      .then(() => run())
      .catch(() => {
        void this.keycloak.login({ redirectUri: this.redirectMiVivienda() });
      });
  }

  reload(): void {
    this.runWithFreshToken(() => {
      this.loading.set(true);
      this.error.set(null);
      this.api
        .list()
        .pipe(
          takeUntilDestroyed(this.destroyRef),
          finalize(() => this.loading.set(false)),
        )
        .subscribe({
          next: (rows) => this.items.set(rows),
          error: () =>
            this.error.set('No se pudieron cargar las viviendas. ¿Está levantada la API (puerto 8082)?'),
        });
    });
  }

  registrar(): void {
    if (
      !this.ubicacionNueva.trim() ||
      this.habitantesNuevo == null ||
      this.habitantesNuevo < 1 ||
      this.estratoNuevo == null ||
      this.estratoNuevo < 1 ||
      this.estratoNuevo > 6
    ) {
      this.error.set('Completa tipo, habitantes, estrato (1–6) y ubicación.');
      return;
    }
    this.runWithFreshToken(() => {
      this.loading.set(true);
      this.error.set(null);
      this.api
        .create({
          tipo: this.tipoNuevo,
          habitantes: this.habitantesNuevo!,
          estrato: this.estratoNuevo!,
          ubicacion: this.ubicacionNueva.trim(),
        })
        .pipe(
          takeUntilDestroyed(this.destroyRef),
          finalize(() => this.loading.set(false)),
        )
        .subscribe({
          next: () => {
            this.ubicacionNueva = '';
            this.estratoNuevo = 3;
            this.reload();
          },
          error: () => this.error.set('No se pudo registrar la vivienda.'),
        });
    });
  }

  startEdit(v: ViviendaDto): void {
    this.editId = v.id;
    this.tipoEdit = v.tipo;
    this.habitantesEdit = v.habitantes;
    this.estratoEdit = v.estrato ?? 3;
    this.ubicacionEdit = v.ubicacion;
    this.zonaEdit = v.zonaClimatica ?? '';
  }

  cancelEdit(): void {
    this.editId = null;
  }

  guardarEdicion(): void {
    if (
      this.editId == null ||
      this.habitantesEdit == null ||
      this.estratoEdit == null ||
      this.estratoEdit < 1 ||
      this.estratoEdit > 6 ||
      !this.ubicacionEdit.trim()
    ) {
      return;
    }
    this.runWithFreshToken(() => {
      this.loading.set(true);
      this.error.set(null);
      this.api
        .update(this.editId!, {
          tipo: this.tipoEdit,
          habitantes: this.habitantesEdit!,
          estrato: this.estratoEdit!,
          ubicacion: this.ubicacionEdit.trim(),
          zonaClimatica: this.zonaEdit.trim() || null,
        })
        .pipe(
          takeUntilDestroyed(this.destroyRef),
          finalize(() => this.loading.set(false)),
        )
        .subscribe({
          next: () => {
            this.editId = null;
            this.reload();
          },
          error: () => this.error.set('No se pudo actualizar la vivienda.'),
        });
    });
  }

  eliminar(v: ViviendaDto): void {
    if (!confirm(`¿Eliminar la vivienda "${v.tipo}" en ${v.ubicacion}?`)) {
      return;
    }
    this.runWithFreshToken(() => {
      this.loading.set(true);
      this.error.set(null);
      this.api
        .delete(v.id)
        .pipe(
          takeUntilDestroyed(this.destroyRef),
          finalize(() => this.loading.set(false)),
        )
        .subscribe({
          next: () => {
            if (this.editId === v.id) {
              this.editId = null;
            }
            this.reload();
          },
          error: () => this.error.set('No se pudo eliminar la vivienda.'),
        });
    });
  }
}
