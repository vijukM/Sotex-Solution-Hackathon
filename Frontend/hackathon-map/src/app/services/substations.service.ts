import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, forkJoin, of, Subject, BehaviorSubject } from 'rxjs';

export interface Station {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
}

export interface BoundsRequest {
  minLat: number;
  maxLat: number;
  minLon: number;
  maxLon: number;
}

export interface StationsByBoundsResult {
  mediumVoltage: Station[];
  highVoltage: Station[];
  distributionTransformers: Station[];
}

export interface StationIdsRequest {
  tsIds: number[];
  ssIds: number[];
  dtIds: number[];
  showTS: boolean;
  showSS: boolean;
  showDT: boolean;
}

export interface MapFilters {
  showSN: boolean;
  showVN: boolean;
  showDT: boolean;
  autoLoad: boolean;
  useClustering: boolean;
  showF33: boolean;
  showF11: boolean;
}

export interface FeederLine {
  feederId: number;
  feederName: string;
  feederType: string;
  sourceStationId: number;
  sourceStationName: string;
  sourceLat: number;
  sourceLon: number;
  targetStationId: number;
  targetStationName: string;
  targetLat: number;
  targetLon: number;
}

export interface StationDetailsDto {
  id: number;
  name: string;
  connectedSsCount: number;
  connectedDtCount: number;
}

export interface FeederLineWithLengthDto {
  feederId: number;
  feederName: string;
  feederType: string;
  averageLengthKm: number;
  sourceLat: number;
  sourceLon: number;
  targetLat: number;
  targetLon: number;
}

export interface DashboardSummary {
  totalTs: number;
  totalSs: number;
  totalDs: number;
  totalF33: number;
  totalF11: number;
  dsWithF11: number;
  dsWithF33: number;
  top5Ss: { name: string; count: number }[];
  isolatedStations: string[];
  tsSsConnections: { tsName: string; ssName: string; f33Name: string }[];
  geoLocations: { name: string; type: string; lat: number; lng: number }[];
}

export interface OutageDto {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  minVoltageA: number;
  minVoltageB: number;
  minVoltageC: number;
  ispadA: number;
  ispadB: number;
  ispadC: number;
  status: string;
}

export interface VoltageTrendDto {
  datum: string | Date;
  avgVoltageA: number | null;
  avgVoltageB: number | null;
  avgVoltageC: number | null;
  minVoltageA: number | null;
  minVoltageB: number | null;
  minVoltageC: number | null;
}

@Injectable({
  providedIn: 'root'
})
export class SubstationsService {
  private readonly apiBase = 'http://localhost:5067/api';

  getAllTransmissionStations(): Observable<Station[]> {
    return this.http.get<Station[]>(`${this.apiBase}/TransmissionStations`);
  }

  getAllSubstations(): Observable<Station[]> {
    return this.http.get<Station[]>(`${this.apiBase}/Substations`);
  }

  getAllDistributionSubstations(): Observable<Station[]> {
    return this.http.get<Station[]>(`${this.apiBase}/DistributionSubstations`);
  }

  getDashboardSummary(): Observable<DashboardSummary> {
    return this.http.get<DashboardSummary>(`${this.apiBase}/Analytics/DashboardSummary`);
  }

  // State for filters
  public filters$ = new BehaviorSubject<MapFilters>({
    showSN: true,
    showVN: true,
    showDT: true,
    autoLoad: false,
    useClustering: true,
    showF33: false,
    showF11: false
  });

  // Triggers map fetch
  public triggerFetch$ = new Subject<void>();

  // Global loading state
  public isLoading$ = new BehaviorSubject<boolean>(false);

  // Global map zoom level tracking
  public mapZoom$ = new BehaviorSubject<number>(12);

  constructor(private readonly http: HttpClient) {}

  getStationsByBounds(
    bounds: BoundsRequest,
    options?: { includeMedium?: boolean; includeHigh?: boolean; includeDT?: boolean }
  ): Observable<StationsByBoundsResult> {
    const params = new HttpParams()
      .set('minLat', bounds.minLat)
      .set('maxLat', bounds.maxLat)
      .set('minLon', bounds.minLon)
      .set('maxLon', bounds.maxLon);

    const includeM = options?.includeMedium ?? true;
    const includeH = options?.includeHigh ?? true;
    const includeDT = options?.includeDT ?? false;

    const observables: any = {};

    if (includeM) {
      observables.mediumVoltage = this.http.get<Station[]>(`${this.apiBase}/Substations/by-bounds`, { params });
    } else {
      observables.mediumVoltage = of([]);
    }

    if (includeH) {
      observables.highVoltage = this.http.get<Station[]>(`${this.apiBase}/TransmissionStations/by-bounds`, { params });
    } else {
      observables.highVoltage = of([]);
    }

    if (includeDT) {
      observables.distributionTransformers = this.http.get<Station[]>(`${this.apiBase}/DistributionSubstations/by-bounds`, { params });
    } else {
      observables.distributionTransformers = of([]);
    }

    return forkJoin(observables) as Observable<StationsByBoundsResult>;
  }

  getF33Lines(request: StationIdsRequest): Observable<FeederLine[]> {
    return this.http.post<FeederLine[]>(`${this.apiBase}/Feeders/F33/by-stations`, request);
  }

  getF11Lines(request: StationIdsRequest): Observable<FeederLine[]> {
    return this.http.post<FeederLine[]>(`${this.apiBase}/Feeders/F11/by-stations`, request);
  }

  getTsDetails(id: number): Observable<StationDetailsDto> {
    return this.http.get<StationDetailsDto>(`${this.apiBase}/TransmissionStations/${id}/details`);
  }

  getTsFeeders(id: number, showF33: boolean = true, showF11: boolean = true): Observable<FeederLineWithLengthDto[]> {
    const params = new HttpParams().set('showF33', showF33).set('showF11', showF11);
    return this.http.get<FeederLineWithLengthDto[]>(`${this.apiBase}/TransmissionStations/${id}/feeders`, { params });
  }

  getSsDetails(id: number): Observable<StationDetailsDto> {
    return this.http.get<StationDetailsDto>((`${this.apiBase}/Substations/${id}/details`));
  }

  getSsFeeders(id: number): Observable<FeederLineWithLengthDto[]> {
    return this.http.get<FeederLineWithLengthDto[]>(`${this.apiBase}/Substations/${id}/feeders`);
  }

  createTransmissionStation(station: Partial<Station>): Observable<Station> {
    return this.http.post<Station>(`${this.apiBase}/TransmissionStations`, station);
  }

  createSubstation(station: Partial<Station>): Observable<Station> {
    return this.http.post<Station>(`${this.apiBase}/Substations`, station);
  }

  createDistributionSubstation(station: any): Observable<any> {
    return this.http.post<any>(`${this.apiBase}/DistributionSubstations`, station);
  }

  getOutages(): Observable<OutageDto[]> {
    return this.http.get<OutageDto[]>(`${this.apiBase}/outages`);
  }

  getOutageTrend(meterId: number, from?: string, to?: string): Observable<VoltageTrendDto[]> {
    let params = new HttpParams();
    if (from) params = params.set('from', from);
    if (to) params = params.set('to', to);
    
    return this.http.get<VoltageTrendDto[]>(`${this.apiBase}/outages/trend/${meterId}`, { params });
  }
}