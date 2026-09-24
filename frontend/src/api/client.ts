/**
 * Unified API Client for MPLADS Intelligence Platform.
 */

import {
  CanonicalWork,
  DetectorDefinition,
  DistrictMetric,
  GovernanceDossier,
  MPProfile,
  PlatformOverview,
  ReviewState,
  StateMapMetric,
  UserProfile,
  VendorProfile,
} from '../types';

const API_BASE = '/api';

class ApiClient {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API error ${response.status}: ${errorText}`);
    }

    return response.json();
  }

  // Auth & Personas
  async getPersonas(): Promise<Record<string, UserProfile>> {
    return this.request<Record<string, UserProfile>>('/auth/personas');
  }

  async switchPersona(
    payload: string | {
      persona_id?: string;
      role?: string;
      state?: string;
      district?: string;
      mp_name?: string;
      constituency?: string;
      strict_isolation?: boolean;
    }
  ): Promise<{ access_token: string; user: UserProfile }> {
    const body = typeof payload === 'string' ? { persona_id: payload } : payload;
    return this.request<{ access_token: string; user: UserProfile }>('/auth/switch-persona', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  // Overview & Macro Trends
  async getOverview(): Promise<PlatformOverview> {
    return this.request<PlatformOverview>('/overview');
  }

  async getTrends(): Promise<any[]> {
    return this.request<any[]>('/overview/trends');
  }

  // Geospatial Map
  async getStateMapMetrics(): Promise<StateMapMetric[]> {
    return this.request<StateMapMetric[]>('/map/states');
  }

  async getDistrictsForState(state: string): Promise<DistrictMetric[]> {
    return this.request<DistrictMetric[]>(`/map/districts?state=${encodeURIComponent(state)}`);
  }

  async getGeoJson(): Promise<any> {
    return this.request<any>('/map/geojson');
  }

  // Works Explorer
  async searchWorks(params: {
    query?: string;
    state?: string;
    district?: string;
    category?: string;
    priority?: string;
    page?: number;
    page_size?: number;
  }): Promise<{ total: number; page: number; page_size: number; total_pages: number; items: CanonicalWork[] }> {
    const searchParams = new URLSearchParams();
    if (params.query) searchParams.set('query', params.query);
    if (params.state) searchParams.set('state', params.state);
    if (params.district) searchParams.set('district', params.district);
    if (params.category) searchParams.set('category', params.category);
    if (params.priority) searchParams.set('priority', params.priority);
    if (params.page) searchParams.set('page', params.page.toString());
    if (params.page_size) searchParams.set('page_size', params.page_size.toString());

    return this.request(`/works?${searchParams.toString()}`);
  }

  async getWorkDetail(recId: string): Promise<any> {
    return this.request(`/works/${recId}`);
  }

  // 5-Question Governance Dossier
  async getDossier(recId: string): Promise<GovernanceDossier> {
    return this.request<GovernanceDossier>(`/dossier/${recId}`);
  }

  getDossierHtmlUrl(recId: string): string {
    return `${API_BASE}/dossier/${recId}/html`;
  }

  // Review Actions & SQLite Persistence
  async getReviewState(recId: string): Promise<ReviewState> {
    return this.request<ReviewState>(`/actions/${recId}`);
  }

  async updateReviewState(
    recId: string,
    payload: { status: string; checked_actions: string[]; auditor_notes?: string; auditor_name?: string }
  ): Promise<ReviewState> {
    return this.request<ReviewState>(`/actions/${recId}`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // Detectors Catalog & Dynamic Simulation Sandbox
  async getDetectors(): Promise<DetectorDefinition[]> {
    return this.request<DetectorDefinition[]>('/detectors');
  }

  async simulateThresholds(params: {
    sla_days: number;
    execution_days: number;
    z_threshold: number;
  }): Promise<any> {
    return this.request<any>('/detectors/simulate', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  // Entity Intelligence
  async searchMps(params: { query?: string; house?: string; state?: string; page?: number; page_size?: number }): Promise<{
    total: number;
    page: number;
    items: MPProfile[];
  }> {
    const sp = new URLSearchParams();
    if (params.query) sp.set('query', params.query);
    if (params.house) sp.set('house', params.house);
    if (params.state) sp.set('state', params.state);
    if (params.page) sp.set('page', params.page.toString());
    if (params.page_size) sp.set('page_size', params.page_size.toString());

    return this.request(`/mps?${sp.toString()}`);
  }

  async getMpDetail(mpName: string): Promise<any> {
    return this.request(`/mps/${encodeURIComponent(mpName)}`);
  }

  async searchVendors(params: { query?: string; hhi_risk?: string; page?: number; page_size?: number }): Promise<{
    total: number;
    page: number;
    items: VendorProfile[];
  }> {
    const sp = new URLSearchParams();
    if (params.query) sp.set('query', params.query);
    if (params.hhi_risk) sp.set('hhi_risk', params.hhi_risk);
    if (params.page) sp.set('page', params.page.toString());
    if (params.page_size) sp.set('page_size', params.page_size.toString());

    return this.request(`/vendors?${sp.toString()}`);
  }

  async getVendorDetail(vendorName: string): Promise<any> {
    return this.request(`/vendors/${encodeURIComponent(vendorName)}`);
  }
}

export const api = new ApiClient();
