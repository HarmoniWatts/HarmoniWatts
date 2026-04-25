import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import type {
  DashboardApiEndpoints,
  DashboardAppliancesTopResponse,
  DashboardConsumptionChartResponse,
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
    if (params.householdId) {
      p = p.set('householdId', params.householdId);
    }
    return p;
  }
}
