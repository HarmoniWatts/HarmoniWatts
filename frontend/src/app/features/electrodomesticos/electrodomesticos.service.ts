import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface TipoCatalogoItem {
  id: number;
  codigo: string;
  nombreEs: string;
  orden: number;
  activo: boolean;
}

export interface MarcaCatalogoItem {
  id: number;
  nombre: string;
  orden: number;
  activo: boolean;
}

export interface CatalogosResponse {
  tipos: TipoCatalogoItem[];
  marcas: MarcaCatalogoItem[];
}

export interface ElectrodomesticoDto {
  id: number;
  idVivienda: number;
  idTipoPredefinido: number;
  tipoCodigo: string;
  tipoNombre: string;
  idMarcaPredefinida: number | null;
  marcaNombre: string | null;
  marcaOtro: string | null;
  nombre: string;
  consumoKwhDia: number;
  usoSemanal: number;
  horarioHabitual: string | null;
  esDesplazable: boolean;
  activo: boolean;
  potenciaW?: number | null;
  consumoAjustadoKwhMes?: number | null;
  horarios?: HorarioUso[];
}

/** Franja de uso: 1 = lunes … 7 = domingo; si fin <= inicio cruza la medianoche. */
export interface HorarioUso {
  diaSemana: number;
  horaInicio: string;
  horaFin: string;
}

export type FuenteEstimacion =
  | 'HORARIO_POTENCIA'
  | 'HORARIO_CONSUMO'
  | 'PROMEDIO_DIARIO'
  | 'AJUSTE_USUARIO';

export interface EstimacionElectrodomestico {
  id: number;
  nombre: string;
  tipoCodigo: string;
  tipoNombre: string;
  activo: boolean;
  optimizable: boolean;
  fuente: FuenteEstimacion;
  potenciaW: number | null;
  horasSemana: number;
  kwhDia: number;
  kwhSemana: number;
  kwhMes: number;
  kwhMesCalculado: number;
  porcentaje: number;
  ranking: number;
  /** kWh por [día 0=lunes][hora 0–23] en una semana típica. */
  perfilSemanal: number[][];
}

export interface EstimacionViviendaResponse {
  idVivienda: number;
  diasPorMes: number;
  totalKwhDia: number;
  totalKwhMes: number;
  perfilSemanal: number[][];
  electrodomesticos: EstimacionElectrodomestico[];
}

export interface ElectrodomesticoCreatePayload {
  idTipoPredefinido: number;
  idMarcaPredefinida?: number | null;
  marcaOtro?: string | null;
  nombre?: string | null;
  consumoKwhDia: number;
  usoSemanal: number;
  horarioHabitual?: string | null;
  esDesplazable?: boolean | null;
  potenciaW?: number | null;
  consumoAjustadoKwhMes?: number | null;
  horarios?: HorarioUso[] | null;
}

export interface ElectrodomesticoUpdatePayload extends ElectrodomesticoCreatePayload {
  activo?: boolean | null;
}

export interface VisionAnalysisResponse {
  marcaDetectada: string | null;
  modeloDetectado: string | null;
  tipoSugerido: string | null;
  /** Potencia leída de la placa (W). */
  potenciaWDetectada: number | null;
  /** Consumo de la etiqueta energética RETIQ (kWh/mes). */
  consumoKwhMesDetectado: number | null;
  confianza: number | null;
  fuenteConsumo: string | null;
  idTipoPredefinido: number | null;
  tipoNombre: string | null;
  idMarcaPredefinida: number | null;
  marcaOtro: string | null;
  nombreSugerido: string | null;
  bajaConfianza: boolean | null;
  advertencia: string | null;
}

@Injectable({ providedIn: 'root' })
export class ElectrodomesticosService {
  private readonly http = inject(HttpClient);

  private root(): string {
    return (environment.electrodomesticosApiBaseUrl ?? '').replace(/\/$/, '');
  }

  getCatalogos(): Observable<CatalogosResponse> {
    return this.http.get<CatalogosResponse>(`${this.root()}/api/v1/electrodomesticos/catalogos`);
  }

  list(viviendaId: number): Observable<ElectrodomesticoDto[]> {
    return this.http.get<ElectrodomesticoDto[]>(
      `${this.root()}/api/v1/viviendas/${viviendaId}/electrodomesticos`,
    );
  }

  /** Ranking, distribución y perfil horario estimados (HAR-20). */
  estimacion(viviendaId: number): Observable<EstimacionViviendaResponse> {
    return this.http.get<EstimacionViviendaResponse>(
      `${this.root()}/api/v1/viviendas/${viviendaId}/electrodomesticos/estimacion`,
    );
  }

  create(viviendaId: number, body: ElectrodomesticoCreatePayload): Observable<ElectrodomesticoDto> {
    return this.http.post<ElectrodomesticoDto>(
      `${this.root()}/api/v1/viviendas/${viviendaId}/electrodomesticos`,
      body,
    );
  }

  update(
    viviendaId: number,
    electroId: number,
    body: ElectrodomesticoUpdatePayload,
  ): Observable<ElectrodomesticoDto> {
    return this.http.put<ElectrodomesticoDto>(
      `${this.root()}/api/v1/viviendas/${viviendaId}/electrodomesticos/${electroId}`,
      body,
    );
  }

  delete(viviendaId: number, electroId: number): Observable<void> {
    return this.http.delete<void>(
      `${this.root()}/api/v1/viviendas/${viviendaId}/electrodomesticos/${electroId}`,
    );
  }

  analizarImagen(file: File): Observable<VisionAnalysisResponse> {
    const form = new FormData();
    form.append('imagen', file, file.name);
    return this.http.post<VisionAnalysisResponse>(
      `${this.root()}/api/v1/electrodomesticos/vision/analizar`,
      form,
    );
  }
}
