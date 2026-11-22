import { CommonModule } from '@angular/common';
import { Component, computed, DestroyRef, inject, OnInit, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { finalize } from 'rxjs/operators';
import Keycloak from 'keycloak-js';
import type { ViviendaDto } from '../vivienda/vivienda.service';
import { ViviendaService } from '../vivienda/vivienda.service';
import { DIAS_CORTOS, duracionHoras, sum } from './gestion/estimacion.util';
import { FRANJA_DEFECTO, HorarioEditorComponent } from './horario-editor/horario-editor.component';
import {
  potenciaDesdeEtiqueta,
  PotenciaInputComponent,
  TIPOS_CON_COMPRESOR,
} from './potencia-input/potencia-input.component';
import type {
  CatalogosResponse,
  ElectrodomesticoDto,
  HorarioUso,
  MarcaCatalogoItem,
  TipoCatalogoItem,
  VisionAnalysisResponse,
} from './electrodomesticos.service';
import { ElectrodomesticosService } from './electrodomesticos.service';

const TIPO_OTRO = 'OTRO';

@Component({
  selector: 'app-electrodomesticos-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, HorarioEditorComponent, PotenciaInputComponent],
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
  readonly visionLoading = signal(false);
  readonly visionError = signal<string | null>(null);
  readonly visionAdvertencia = signal<string | null>(null);
  /** Qué dato de consumo se tomó de la foto y cómo se convirtió. */
  readonly visionNota = signal<string | null>(null);
  readonly visionPreviewUrl = signal<string | null>(null);
  readonly cameraActive = signal(false);
  readonly viviendas = signal<ViviendaDto[]>([]);
  readonly catalogos = signal<CatalogosResponse | null>(null);
  readonly items = signal<ElectrodomesticoDto[]>([]);

  selectedViviendaId: number | null = null;
  editingId: number | null = null;
  /** Datos de estimación (HAR-20) que este formulario no edita pero debe conservar al guardar. */
  private editingExtras: Pick<ElectrodomesticoDto, 'consumoAjustadoKwhMes'> = {};

  idTipoPredefinido: number | null = null;
  idMarcaPredefinida: number | null = null;
  marcaOtro = '';
  nombre = '';
  /** Franjas de uso semanales; vacío = siempre encendido (HAR-20). */
  readonly horarios = signal<HorarioUso[]>([{ ...FRANJA_DEFECTO }]);
  /** Potencia en W: único dato de consumo que se pide (HAR-20). */
  readonly potenciaW = signal<number | null>(null);
  /** Horas de uso por semana según el horario (168 = siempre encendido). */
  readonly horasSemana = computed(() => {
    const hs = this.horarios();
    return hs.length ? sum(hs.map(duracionHoras)) : 168;
  });
  esDesplazable = false;
  activo = true;


  private mediaStream: MediaStream | null = null;
  private pendingVisionFile: File | null = null;

  ngOnInit(): void {
    this.runWithFreshToken(() => {
      this.loadViviendas();
      this.loadCatalogos();
    });
    this.destroyRef.onDestroy(() => this.stopCamera());
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
    this.editingExtras = {};
    this.idTipoPredefinido = this.tipos()[0]?.id ?? null;
    this.idMarcaPredefinida = null;
    this.marcaOtro = '';
    this.nombre = '';
    this.potenciaW.set(null);
    this.horarios.set([{ ...FRANJA_DEFECTO }]);
    this.esDesplazable = false;
    this.activo = true;
    this.clearVisionState();
  }

  /** W que dan `kwhDia` en promedio con el horario actual. */
  private wattsDesdeKwhDia(kwhDia: number | null | undefined): number | null {
    if (!kwhDia || kwhDia <= 0) return null;
    return Math.round((kwhDia * 1000 * 7) / this.horasSemana());
  }

  /** El horario sigue siendo la franja inicial (el usuario no lo ha tocado). */
  private horarioPorDefecto(): boolean {
    const hs = this.horarios();
    return (
      hs.length === 1 &&
      hs[0]!.diaSemana === FRANJA_DEFECTO.diaSemana &&
      hs[0]!.horaInicio === FRANJA_DEFECTO.horaInicio &&
      hs[0]!.horaFin === FRANJA_DEFECTO.horaFin
    );
  }

  /** Texto corto del horario para la tabla. */
  resumenHorario(row: ElectrodomesticoDto): string {
    const hs = row.horarios ?? [];
    if (!hs.length) return 'Siempre encendido';
    const dias = [...new Set(hs.map((h) => h.diaSemana))].sort((a, b) => a - b);
    const horas = sum(hs.map(duracionHoras));
    const diasTxt = dias.length === 7 ? 'Todos los días' : dias.map((d) => DIAS_CORTOS[d - 1]).join(', ');
    return `${diasTxt} · ${horas.toLocaleString('es-CO', { maximumFractionDigits: 1 })} h/sem`;
  }

  clearVisionState(): void {
    this.visionError.set(null);
    this.visionAdvertencia.set(null);
    this.visionNota.set(null);
    this.pendingVisionFile = null;
    this.revokePreview();
    this.stopCamera();
  }

  private revokePreview(): void {
    const url = this.visionPreviewUrl();
    if (url) {
      URL.revokeObjectURL(url);
    }
    this.visionPreviewUrl.set(null);
  }

  async iniciarCamara(videoEl: HTMLVideoElement): Promise<void> {
    this.visionError.set(null);
    if (!navigator.mediaDevices?.getUserMedia) {
      this.visionError.set('Tu navegador no soporta acceso a la cámara.');
      return;
    }
    try {
      this.stopCamera();
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
        audio: false,
      });
      this.mediaStream = stream;
      videoEl.srcObject = stream;
      await videoEl.play();
      this.cameraActive.set(true);
    } catch {
      this.visionError.set('No se pudo acceder a la cámara. Revisa permisos o usa «Subir imagen».');
      this.cameraActive.set(false);
    }
  }

  stopCamera(): void {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((t) => t.stop());
      this.mediaStream = null;
    }
    this.cameraActive.set(false);
  }

  capturarDesdeCamara(videoEl: HTMLVideoElement, canvasEl: HTMLCanvasElement): void {
    if (!this.cameraActive() || !videoEl.videoWidth) {
      return;
    }
    canvasEl.width = videoEl.videoWidth;
    canvasEl.height = videoEl.videoHeight;
    const ctx = canvasEl.getContext('2d');
    if (!ctx) {
      return;
    }
    ctx.drawImage(videoEl, 0, 0);
    canvasEl.toBlob(
      (blob) => {
        if (!blob) {
          this.visionError.set('No se pudo capturar la foto.');
          return;
        }
        const file = new File([blob], 'captura-electrodomestico.jpg', { type: 'image/jpeg' });
        this.setVisionFile(file);
        this.stopCamera();
      },
      'image/jpeg',
      0.92,
    );
  }

  onArchivoSeleccionado(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    input.value = '';
    if (!file) {
      return;
    }
    if (!file.type.startsWith('image/')) {
      this.visionError.set('Selecciona un archivo de imagen (JPEG, PNG, WebP).');
      return;
    }
    this.setVisionFile(file);
  }

  private setVisionFile(file: File): void {
    this.pendingVisionFile = file;
    this.revokePreview();
    this.visionPreviewUrl.set(URL.createObjectURL(file));
    this.visionError.set(null);
    this.visionAdvertencia.set(null);
  }

  analizarImagenSeleccionada(): void {
    if (!this.pendingVisionFile) {
      this.visionError.set('Primero captura o sube una imagen.');
      return;
    }
    this.runWithFreshToken(() => {
      this.visionLoading.set(true);
      this.visionError.set(null);
      this.visionAdvertencia.set(null);
      this.electroApi
        .analizarImagen(this.pendingVisionFile!)
        .pipe(
          takeUntilDestroyed(this.destroyRef),
          finalize(() => this.visionLoading.set(false)),
        )
        .subscribe({
          next: (res) => this.aplicarSugerenciasVision(res),
          error: () => {
            this.visionError.set(
              'No se pudo analizar la imagen. Intenta con una foto más clara del electrodoméstico o su etiqueta de potencia.',
            );
          },
        });
    });
  }

  private aplicarSugerenciasVision(res: VisionAnalysisResponse): void {
    if (res.idTipoPredefinido != null) {
      this.idTipoPredefinido = res.idTipoPredefinido;
    }
    if (res.idMarcaPredefinida != null) {
      this.idMarcaPredefinida = res.idMarcaPredefinida;
    }
    if (res.marcaOtro) {
      this.marcaOtro = res.marcaOtro;
    }
    if (res.nombreSugerido && this.esTipoOtro()) {
      this.nombre = res.nombreSugerido;
    } else if (res.modeloDetectado && !this.esTipoOtro()) {
      // modelo como referencia en nombre si el tipo no es OTRO (no obligatorio guardar)
    }
    // Neveras y congeladores están siempre encendidos: si el horario sigue en el valor por defecto, se ajusta
    const tipo = this.tipoSeleccionado()?.codigo ?? null;
    if ((tipo === 'NEVERA' || tipo === 'CONGELADOR') && this.horarioPorDefecto()) {
      this.horarios.set([]);
    }
    const sugerida = potenciaDesdeEtiqueta(
      res.potenciaWDetectada,
      res.consumoKwhMesDetectado,
      tipo,
      this.horasSemana(),
    );
    this.visionNota.set(null);
    if (sugerida) {
      this.potenciaW.set(sugerida.w);
      this.visionNota.set(
        sugerida.origen === 'etiqueta'
          ? `Leímos ${res.consumoKwhMesDetectado} kWh/mes en la etiqueta: equivale a ${sugerida.w} W con tu horario (${Math.round(this.horasSemana())} h/semana).` +
              (TIPOS_CON_COMPRESOR.includes(tipo ?? '') ? ' En aparatos con compresor es más preciso que la potencia de la placa.' : '')
          : `Leímos ${sugerida.w} W en la placa del aparato.`,
      );
    }
    if (res.bajaConfianza && res.advertencia) {
      this.visionAdvertencia.set(res.advertencia);
    } else if (res.advertencia) {
      this.visionAdvertencia.set(res.advertencia);
    } else if (res.confianza != null && res.confianza < 0.7) {
      this.visionAdvertencia.set(
        'Confianza baja en el análisis. Revisa los campos antes de guardar.',
      );
    }
    this.error.set(null);
  }

  startCreate(): void {
    this.resetForm();
  }

  startEdit(row: ElectrodomesticoDto): void {
    this.editingId = row.id;
    this.editingExtras = { consumoAjustadoKwhMes: row.consumoAjustadoKwhMes ?? null };
    this.idTipoPredefinido = row.idTipoPredefinido;
    this.idMarcaPredefinida = row.idMarcaPredefinida;
    this.marcaOtro = row.marcaOtro ?? '';
    this.nombre = row.nombre;
    this.horarios.set((row.horarios ?? []).map((h) => ({ ...h })));
    // Registros anteriores a HAR-20 solo tienen kWh/día: se convierten a W con su horario
    this.potenciaW.set(row.potenciaW ?? this.wattsDesdeKwhDia(row.consumoKwhDia));
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
    const potenciaW = this.potenciaW();
    if (this.idTipoPredefinido == null) {
      this.error.set('Selecciona el tipo de electrodoméstico.');
      return;
    }
    if (potenciaW == null || potenciaW <= 0) {
      this.error.set('Indica la potencia en watts (W). Si tu etiqueta dice kWh/mes, usa la calculadora.');
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

    const horarios = this.horarios();
    if (horarios.some((h) => !h.horaInicio || !h.horaFin)) {
      this.error.set('Completa la hora de inicio y fin de cada franja del horario.');
      return;
    }
    // Columnas legadas: veces por semana = días con uso; horario = inicio de la primera franja
    const diasConUso = horarios.length ? new Set(horarios.map((h) => h.diaSemana)).size : 7;

    const base = {
      idTipoPredefinido: this.idTipoPredefinido,
      idMarcaPredefinida: this.idMarcaPredefinida,
      marcaOtro: this.marcaOtro.trim() || null,
      nombre: this.nombre.trim() || null,
      // El backend lo recalcula con potencia × horario; se envía por compatibilidad
      consumoKwhDia: Math.max(0.0001, Math.round(((potenciaW * this.horasSemana()) / 7 / 1000) * 10000) / 10000),
      usoSemanal: diasConUso,
      horarioHabitual: horarios[0]?.horaInicio ?? null,
      esDesplazable: this.esDesplazable,
      potenciaW,
      horarios,
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
          .update(vid, this.editingId, {
            ...base,
            consumoAjustadoKwhMes: this.editingExtras.consumoAjustadoKwhMes ?? null,
            activo: this.activo,
          })
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

}
