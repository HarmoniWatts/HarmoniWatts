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
}

export interface ElectrodomesticoUpdatePayload extends ElectrodomesticoCreatePayload {
  activo?: boolean | null;
}

export interface VisionAnalysisResponse {
  marcaDetectada: string | null;
  modeloDetectado: string | null;
  tipoSugerido: string | null;
  consumoKwhDiaEstimado: number | null;
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
