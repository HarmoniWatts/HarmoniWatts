import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import type {
  DashboardApiEndpoints,
  AlertsQueryParams,
  DashboardAlertsResponse,
  DashboardAppliancesTopResponse,
  DashboardConsumptionChartResponse,
  DashboardPredictionResponse,
  DashboardQueryParams,
  DashboardRecommendationsResponse,
  DashboardSummaryResponse,
} from './dashboard.models';

@Injectable({ providedIn: 'root' })
export class DashboardService {
  private readonly http = inject(HttpClient);

  private baseUrl(): string {
    const env = environment as typeof environment & { dashboardInsightsBaseUrl?: string };
    const raw = env.dashboardInsightsBaseUrl || env.apiBaseUrl || '';
    return raw.replace(/\/$/, '');
  }

  private url(path: string): string {
    const base = this.baseUrl();
    const p = path.startsWith('/') ? path : `/${path}`;
    return base ? `${base}${p}` : p;
  }

  private endpoints(): DashboardApiEndpoints {
    return environment.dashboardApi;
  }

  getSummary(params?: DashboardQueryParams): Observable<DashboardSummaryResponse> {
    return this.http.get<DashboardSummaryResponse>(this.url(this.endpoints().summaryPath), {
      params: this.toParams(params),
    });
  }

  getConsumptionChart(params?: DashboardQueryParams): Observable<DashboardConsumptionChartResponse> {
    return this.http.get<DashboardConsumptionChartResponse>(this.url(this.endpoints().consumptionChartPath), {
      params: this.toParams(params),
    });
  }

  getRecommendations(
    params?: DashboardQueryParams & { limit?: number },
  ): Observable<DashboardRecommendationsResponse> {
    let httpParams = this.toParams(params);
    if (params?.limit != null) {
      httpParams = httpParams.set('limit', String(params.limit));
    }
    return this.http.get<DashboardRecommendationsResponse>(this.url(this.endpoints().recommendationsPath), {
      params: httpParams,
    });
  }

  getAppliancesTop(
    params?: DashboardQueryParams & { limit?: number },
  ): Observable<DashboardAppliancesTopResponse> {
    let httpParams = this.toParams(params);
    if (params?.limit != null) {
      httpParams = httpParams.set('limit', String(params.limit));
    }
    return this.http.get<DashboardAppliancesTopResponse>(this.url(this.endpoints().appliancesTopPath), {
      params: httpParams,
    });
  }

  /** Predicción vs real y próximos días con su confianza (HAR-25). */
  getPrediction(params: DashboardQueryParams): Observable<DashboardPredictionResponse> {
    return this.http.get<DashboardPredictionResponse>(this.url('/api/v1/dashboard/prediction'), {
      params: this.toParams(params),
    });
  }

  /** Alertas de franja de alto precio y consumo sobre lo habitual (HAR-21). */
  getAlerts(q: AlertsQueryParams): Observable<DashboardAlertsResponse> {
    let p = new HttpParams();
    if (q.noContrato && q.codComercializadora) {
      p = p.set('noContrato', q.noContrato).set('codComercializadora', q.codComercializadora);
    }
    if (q.idZona != null && q.codMercado && q.estrato != null) {
      p = p.set('idZona', String(q.idZona)).set('codMercado', q.codMercado).set('estrato', String(q.estrato));
    }
    if (q.at) {
      p = p.set('at', q.at);
    }
    return this.http.get<DashboardAlertsResponse>(this.url('/api/v1/dashboard/alerts'), { params: p });
  }

  applyRecommendation(id: string): Observable<unknown> {
    const path = this.endpoints().recommendationApplyPathTemplate.replace('{id}', encodeURIComponent(id));
    return this.http.post(this.url(path), {});
  }

  dismissRecommendation(id: string): Observable<unknown> {
    const path = this.endpoints().recommendationDismissPathTemplate.replace('{id}', encodeURIComponent(id));
    return this.http.post(this.url(path), {});
  }

  private toParams(params?: DashboardQueryParams): HttpParams {
    let p = new HttpParams();
    if (!params) {
      return p;
    }
    if (params.date) {
      p = p.set('date', params.date);
    }
    if (params.noContrato && params.codComercializadora) {
      p = p.set('noContrato', params.noContrato).set('codComercializadora', params.codComercializadora);
    }
    return p;
  }
}
