import { CommonModule } from '@angular/common';
import { Component, DestroyRef, inject, OnInit, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { finalize } from 'rxjs/operators';
import Keycloak from 'keycloak-js';
import type { ViviendaDto } from '../vivienda/vivienda.service';
import { ViviendaService } from '../vivienda/vivienda.service';
import type {
  CatalogosResponse,
  ElectrodomesticoDto,
  MarcaCatalogoItem,
  TipoCatalogoItem,
} from './electrodomesticos.service';
import { ElectrodomesticosService } from './electrodomesticos.service';

const TIPO_OTRO = 'OTRO';

@Component({
  selector: 'app-electrodomesticos-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './electrodomesticos-page.component.html',
  styleUrl: './electrodomesticos-page.component.css',
})
export class ElectrodomesticosPageComponent implements OnInit {
  private readonly viviendaApi = inject(ViviendaService);
  private readonly electroApi = inject(ElectrodomesticosService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly keycloak = inject(Keycloak);

  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly viviendas = signal<ViviendaDto[]>([]);
  readonly catalogos = signal<CatalogosResponse | null>(null);
  readonly items = signal<ElectrodomesticoDto[]>([]);

  selectedViviendaId: number | null = null;
  editingId: number | null = null;

  idTipoPredefinido: number | null = null;
  idMarcaPredefinida: number | null = null;
  marcaOtro = '';
  nombre = '';
  potenciaW: number | null = null;
  usoSemanal: number | null = 3;
  /** Valor para input type=time (HH:mm); se envía como horarioHabitual al API. */
  horarioHabitual = '';
  esDesplazable = false;
  activo = true;

  ngOnInit(): void {
    this.runWithFreshToken(() => {
      this.loadViviendas();
      this.loadCatalogos();
    });
  }

  private redirectHere(): string {
    return `${window.location.origin}/cuenta/electrodomesticos`;
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
        void this.keycloak.login({ redirectUri: this.redirectHere() });
      });
  }

  onViviendaChange(): void {
    if (this.selectedViviendaId == null) {
      this.items.set([]);
      return;
    }
    this.runWithFreshToken(() => this.reloadList());
  }

  private loadViviendas(): void {
    this.loading.set(true);
    this.error.set(null);
    this.viviendaApi
      .list()
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: (rows) => {
          this.viviendas.set(rows);
          if (rows.length && this.selectedViviendaId == null) {
            this.selectedViviendaId = rows[0]!.id;
            this.reloadList();
          }
        },
        error: () =>
          this.error.set(
            'No se pudieron cargar las viviendas. Registra al menos una en «Mi vivienda».',
          ),
      });
  }

  private loadCatalogos(): void {
    this.electroApi
      .getCatalogos()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (c) => {
          this.catalogos.set(c);
          if (this.idTipoPredefinido == null && c.tipos.length) {
            this.idTipoPredefinido = c.tipos[0]!.id;
          }
        },
        error: () => this.error.set('No se pudieron cargar los catálogos de electrodomésticos.'),
      });
  }

  reloadList(): void {
    if (this.selectedViviendaId == null) {
      return;
    }
    this.loading.set(true);
    this.error.set(null);
    this.electroApi
      .list(this.selectedViviendaId)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: (rows) => this.items.set(rows),
        error: () =>
          this.error.set(
            'No se pudieron cargar los electrodomésticos. ¿Está levantada la API (8083) y aplicada la migración SQL?',
          ),
      });
  }

  tipos(): TipoCatalogoItem[] {
    return this.catalogos()?.tipos ?? [];
  }

  marcas(): MarcaCatalogoItem[] {
    return this.catalogos()?.marcas ?? [];
  }

  tipoSeleccionado(): TipoCatalogoItem | undefined {
    if (this.idTipoPredefinido == null) {
      return undefined;
    }
    return this.tipos().find((t) => t.id === this.idTipoPredefinido);
  }

  marcaSeleccionada(): MarcaCatalogoItem | undefined {
    if (this.idMarcaPredefinida == null) {
      return undefined;
    }
    return this.marcas().find((m) => m.id === this.idMarcaPredefinida);
  }

  esTipoOtro(): boolean {
    return this.tipoSeleccionado()?.codigo === TIPO_OTRO;
  }

  esMarcaOtro(): boolean {
    const n = this.marcaSeleccionada()?.nombre?.trim().toLowerCase();
    return n === 'otro';
  }

  resetForm(): void {
    this.editingId = null;
    this.idTipoPredefinido = this.tipos()[0]?.id ?? null;
    this.idMarcaPredefinida = null;
    this.marcaOtro = '';
    this.nombre = '';
    this.potenciaW = null;
    this.usoSemanal = 3;
    this.horarioHabitual = '';
    this.esDesplazable = false;
    this.activo = true;
  }

  startCreate(): void {
    this.resetForm();
  }

  startEdit(row: ElectrodomesticoDto): void {
    this.editingId = row.id;
    this.idTipoPredefinido = row.idTipoPredefinido;
    this.idMarcaPredefinida = row.idMarcaPredefinida;
    this.marcaOtro = row.marcaOtro ?? '';
    this.nombre = row.nombre;
    this.potenciaW = row.potenciaW;
    this.usoSemanal = row.usoSemanal;
    this.horarioHabitual = this.toTimeInputValue(row.horarioHabitual);
    this.esDesplazable = !!row.esDesplazable;
    this.activo = row.activo !== false;
  }

  cancelarEdicion(): void {
    this.resetForm();
  }

  guardar(): void {
    if (this.selectedViviendaId == null) {
      this.error.set('Selecciona una vivienda.');
      return;
    }
    if (this.idTipoPredefinido == null || this.potenciaW == null || this.usoSemanal == null) {
      this.error.set('Completa tipo, potencia (W) y uso semanal.');
      return;
    }
    if (this.esTipoOtro() && !this.nombre.trim()) {
      this.error.set('Indica el nombre del electrodoméstico personalizado.');
      return;
    }
    if (this.esMarcaOtro() && !this.marcaOtro.trim()) {
      this.error.set('Indica la marca en texto cuando eliges «Otro».');
      return;
    }

    const base = {
      idTipoPredefinido: this.idTipoPredefinido,
      idMarcaPredefinida: this.idMarcaPredefinida,
      marcaOtro: this.marcaOtro.trim() || null,
      nombre: this.nombre.trim() || null,
      potenciaW: this.potenciaW,
      usoSemanal: this.usoSemanal,
      horarioHabitual: this.horarioHabitual.trim() || null,
      esDesplazable: this.esDesplazable,
    };

    this.runWithFreshToken(() => {
      this.loading.set(true);
      this.error.set(null);
      const vid = this.selectedViviendaId!;
      if (this.editingId == null) {
        this.electroApi
          .create(vid, base)
          .pipe(
            takeUntilDestroyed(this.destroyRef),
            finalize(() => this.loading.set(false)),
          )
          .subscribe({
            next: () => {
              this.resetForm();
              this.reloadList();
            },
            error: () => this.error.set('No se pudo registrar el electrodoméstico.'),
          });
      } else {
        this.electroApi
          .update(vid, this.editingId, { ...base, activo: this.activo })
          .pipe(
            takeUntilDestroyed(this.destroyRef),
            finalize(() => this.loading.set(false)),
          )
          .subscribe({
            next: () => {
              this.resetForm();
              this.reloadList();
            },
            error: () => this.error.set('No se pudo actualizar el electrodoméstico.'),
          });
      }
    });
  }

  eliminar(row: ElectrodomesticoDto): void {
    const viviendaId = this.selectedViviendaId;
    if (viviendaId == null) {
      return;
    }
    if (!confirm(`¿Eliminar «${row.nombre}»?`)) {
      return;
    }
    this.runWithFreshToken(() => {
      this.loading.set(true);
      this.error.set(null);
      this.electroApi
        .delete(viviendaId, row.id)
        .pipe(
          takeUntilDestroyed(this.destroyRef),
          finalize(() => this.loading.set(false)),
        )
        .subscribe({
          next: () => {
            if (this.editingId === row.id) {
              this.resetForm();
            }
            this.reloadList();
          },
          error: () => this.error.set('No se pudo eliminar.'),
        });
    });
  }

  /** API devuelve `HH:mm:ss`; input type=time usa `HH:mm`. */
  private toTimeInputValue(raw: string | null | undefined): string {
    if (!raw?.trim()) {
      return '';
    }
    const p = raw.trim().split(':');
    if (p.length < 2) {
      return '';
    }
    const h = p[0]!.padStart(2, '0');
    const m = p[1]!.padStart(2, '0').slice(0, 2);
    return `${h}:${m}`;
  }
}
