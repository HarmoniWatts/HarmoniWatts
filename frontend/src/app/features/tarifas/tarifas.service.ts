import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, shareReplay } from 'rxjs';
import { environment } from '../../../environments/environment';
import type {
  CalendarioTarifasResponse,
  CiudadTarifaria,
  TarifaUbicacionResponse,
  UbicacionTarifaria,
} from './tarifas.models';

@Injectable({ providedIn: 'root' })
export class TarifasService {
  private readonly http = inject(HttpClient);

  /** El catálogo de ciudades casi no cambia: una sola petición por sesión. */
  private ciudades$?: Observable<CiudadTarifaria[]>;

  private baseUrl(): string {
    const root = (environment.tariffApiBaseUrl ?? '').replace(/\/$/, '');
    return `${root}/api/v1/tariff/ubicacion`;
  }

  listCiudades(): Observable<CiudadTarifaria[]> {
    this.ciudades$ ??= this.http
      .get<CiudadTarifaria[]>(`${this.baseUrl()}/ciudades`)
      .pipe(shareReplay({ bufferSize: 1, refCount: false }));
    return this.ciudades$;
  }

  /** Tarifa vigente (24 h, monomía y componentes) para un día. */
  getTarifa(ubicacion: UbicacionTarifaria, fecha?: string): Observable<TarifaUbicacionResponse> {
    let params = this.ubicacionParams(ubicacion);
    if (fecha) {
      params = params.set('fecha', fecha);
    }
    return this.http.get<TarifaUbicacionResponse>(`${this.baseUrl()}/tarifa`, { params });
  }

  getCalendario(ubicacion: UbicacionTarifaria, anio: number): Observable<CalendarioTarifasResponse> {
    const params = this.ubicacionParams(ubicacion).set('anio', String(anio));
    return this.http.get<CalendarioTarifasResponse>(`${this.baseUrl()}/calendario`, { params });
  }

  private ubicacionParams(u: UbicacionTarifaria): HttpParams {
    return new HttpParams()
      .set('id_zona', String(u.idZona))
      .set('cod_mercado', u.codMercado)
      .set('estrato', String(u.estrato));
  }
}
