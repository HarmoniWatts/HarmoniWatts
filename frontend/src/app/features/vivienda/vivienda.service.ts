import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface ViviendaDto {
  id: number;
  tipo: string;
  habitantes: number;
  /** Estrato socioeconómico (1–6). */
  estrato: number;
  ubicacion: string;
  zonaClimatica?: string | null;
  /** Municipio (catálogo de tariff-service); va junto con `codMercado`. */
  idZona?: number | null;
  /** Mercado de comercialización: con el estrato define la tarifa. */
  codMercado?: string | null;
  numeroContrato?: string | null;
  fechaRegistro?: string | null;
}

export interface ViviendaCreatePayload {
  tipo: string;
  habitantes: number;
  estrato: number;
  ubicacion: string;
  idZona?: number | null;
  codMercado?: string | null;
  numeroContrato?: string | null;
}

export interface ViviendaUpdatePayload extends ViviendaCreatePayload {
  zonaClimatica?: string | null;
}

@Injectable({ providedIn: 'root' })
export class ViviendaService {
  private readonly http = inject(HttpClient);

  private baseUrl(): string {
    const root = (environment.viviendaApiBaseUrl ?? '').replace(/\/$/, '');
    return `${root}/api/v1/viviendas`;
  }

  list(): Observable<ViviendaDto[]> {
    return this.http.get<ViviendaDto[]>(this.baseUrl());
  }

  create(body: ViviendaCreatePayload): Observable<ViviendaDto> {
    return this.http.post<ViviendaDto>(this.baseUrl(), body);
  }

  update(id: number, body: ViviendaUpdatePayload): Observable<ViviendaDto> {
    return this.http.put<ViviendaDto>(`${this.baseUrl()}/${id}`, body);
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl()}/${id}`);
  }
}
