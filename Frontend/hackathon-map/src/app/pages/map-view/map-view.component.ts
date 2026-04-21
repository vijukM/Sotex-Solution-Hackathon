import { Component, OnInit, OnDestroy } from '@angular/core';
import { finalize, Subscription, forkJoin, switchMap, of, map, Observable } from 'rxjs';
import * as L from 'leaflet';
import 'leaflet.markercluster';
import { Station, SubstationsService, MapFilters, FeederLine, StationDetailsDto, FeederLineWithLengthDto } from '../../services/substations.service';

type ToastType = 'success' | 'error' | 'info';

interface ToastMessage {
  id: number;
  text: string;
  type: ToastType;
}

@Component({
  selector: 'app-map-view',
  templateUrl: './map-view.component.html',
  styleUrls: ['./map-view.component.scss']
})
export class MapViewComponent implements OnInit, OnDestroy {
  private map?: L.Map;
  private outagesMap = new Map<number, any>();
  private subs = new Subscription();
  private filters: MapFilters = { showSN: true, showVN: true, showDT: true, autoLoad: false, useClustering: true, showF33: false, showF11: false };

  private readonly mockMediumVoltage: Station[] = [
    { id: 1001, name: 'SN Lagos Ikeja', latitude: 6.6018, longitude: 3.3515 },
    { id: 1002, name: 'SN Abuja Central', latitude: 9.0765, longitude: 7.3986 },
    { id: 1003, name: 'SN Kano North', latitude: 12.0022, longitude: 8.5311 },
    { id: 1004, name: 'SN Port Harcourt East', latitude: 4.8272, longitude: 7.0335 },
    { id: 1005, name: 'SN Ibadan West', latitude: 7.3846, longitude: 3.9001 },
    { id: 1006, name: 'SN Kaduna South', latitude: 10.4874, longitude: 7.4285 },
    { id: 1007, name: 'SN Benin City Ring', latitude: 6.336, longitude: 5.6258 },
    { id: 1008, name: 'SN Jos Plateau', latitude: 9.8966, longitude: 8.8583 },
    { id: 1009, name: 'SN Maiduguri Central', latitude: 11.8452, longitude: 13.1426 },
    { id: 1010, name: 'SN Enugu Main', latitude: 6.4531, longitude: 7.5145 }
  ];

  private readonly mockHighVoltage: Station[] = [
    { id: 2001, name: 'VN Lagos Coastal', latitude: 6.4323, longitude: 3.4046 },
    { id: 2002, name: 'VN Abuja Ring', latitude: 9.1391, longitude: 7.4461 },
    { id: 2003, name: 'VN Kano Hub', latitude: 11.9876, longitude: 8.4764 },
    { id: 2004, name: 'VN Calabar Delta', latitude: 4.9584, longitude: 8.322 },
    { id: 2005, name: 'VN Warri South', latitude: 5.5358, longitude: 5.7811 },
    { id: 2006, name: 'VN Sokoto Link', latitude: 13.0582, longitude: 5.2339 },
    { id: 2007, name: 'VN Ilorin Gate', latitude: 8.4897, longitude: 4.5962 },
    { id: 2008, name: 'VN Onitsha Cross', latitude: 6.1512, longitude: 6.8082 },
    { id: 2009, name: 'VN Uyo Main', latitude: 5.0351, longitude: 7.9312 },
    { id: 2010, name: 'VN Yola North', latitude: 9.2035, longitude: 12.4954 }
  ];

  private readonly mockDistributionTransformers: Station[] = [
    { id: 3001, name: 'DT Abuja CBD North', latitude: 9.0895, longitude: 7.4025 },
    { id: 3002, name: 'DT Abuja CBD South', latitude: 9.0635, longitude: 7.3952 },
    { id: 3003, name: 'DT Wuse II', latitude: 9.0743, longitude: 7.4159 },
    { id: 3004, name: 'DT Garki I', latitude: 9.0437, longitude: 7.4461 },
    { id: 3005, name: 'DT Garki II', latitude: 9.0282, longitude: 7.4565 },
    { id: 3006, name: 'DT Maitama Main', latitude: 9.1084, longitude: 7.4372 },
    { id: 3007, name: 'DT Asokoro', latitude: 9.0163, longitude: 7.5041 },
    { id: 3008, name: 'DT Ikoyi Link', latitude: 9.0923, longitude: 7.3845 },
    { id: 3009, name: 'DT Gwarinpa Ring', latitude: 9.0814, longitude: 7.3621 },
    { id: 3010, name: 'DT Kubwa East', latitude: 9.1645, longitude: 7.3284 }
  ];

  private readonly baseLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors'
  });

  private readonly mediumVoltageIcon = L.icon({
    iconUrl: 'assets/SS.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
    iconSize: [38, 38],
    iconAnchor: [17, 34],
    popupAnchor: [0, -34],
    shadowSize: [42, 42]
  });

  private readonly highVoltageIcon = L.icon({
    iconUrl: 'assets/TS.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
    iconSize: [40, 40],
    iconAnchor: [20, 40],
    popupAnchor: [0, -40],
    shadowSize: [50, 50]
  });

  private readonly distributionTransformerIcon = L.icon({
    iconUrl: 'assets/DS.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
    iconSize: [20, 20],
    iconAnchor: [10, 20],
    popupAnchor: [0, -20],
    shadowSize: [25, 25]
  });

  options = {
    layers: [this.baseLayer],
    zoom: 12,
    center: L.latLng(9.1065, 7.3986)
  };

  private stationLinesLayer = L.featureGroup();
  private endStationsLayer = L.featureGroup();
  layers: L.Layer[] = [this.baseLayer, this.stationLinesLayer, this.endStationsLayer];
  isLoading = false;
  autoLoadOnMove = false;
  useClustering = true;
  showMediumVoltage = true;
  showHighVoltage = true;
  showDistributionTransformers = true;
  showF33 = false;
  showF11 = false;
  toasts: ToastMessage[] = [];

  // Add Station Modal State
  showAddStationModal = false;
  isPickingLocation = false;
  newStation: any = {
    type: 'TS',
    name: '',
    latitude: null,
    longitude: null,
    nameplateRating: null
  };
  
  // Handler for reading coordinates
  private onMapClickHandler = (e: L.LeafletMouseEvent) => {
    if (this.isPickingLocation) {
      this.newStation.latitude = e.latlng.lat;
      this.newStation.longitude = e.latlng.lng;
      this.isPickingLocation = false;
      this.showAddStationModal = true;
    }
  };

  constructor(private readonly substationsService: SubstationsService) {}

  ngOnInit(): void {
    this.subs.add(
      this.substationsService.filters$.subscribe(f => {
        this.showMediumVoltage = f.showSN;
        this.showHighVoltage = f.showVN;
        this.showDistributionTransformers = f.showDT;
        this.autoLoadOnMove = f.autoLoad;
        this.useClustering = f.useClustering;
        this.showF33 = f.showF33;
        this.showF11 = f.showF11;
        
        // Remove this if we don't want strict auto-re-rendering on every checkbox tick without explicit fetch
      })
    );

    this.subs.add(
      this.substationsService.triggerFetch$.subscribe(() => {
        this.showStationsInView();
      })
    );
  }

  ngOnDestroy(): void {
    this.subs.unsubscribe();
    if (this.map) {
      this.map.off('click', this.onMapClickHandler);
    }
  }

  onMapReady(map: L.Map): void {
    this.map = map;

    this.substationsService.mapZoom$.next(map.getZoom());

    map.on('zoomend', () => {
      this.substationsService.mapZoom$.next(map.getZoom());
    });

    map.on('click', this.onMapClickHandler);

    setTimeout(() => {
      this.map?.invalidateSize();
      this.loadOutages();
    }, 0);
  }

  // Load and display outages with pulsing markers
  private loadOutages(): void {
    if (!this.map) return;

    this.substationsService.getOutages().subscribe({
      next: (outages: any[]) => {
        this.outagesMap.clear();
        outages.forEach(outage => {
          this.outagesMap.set(outage.id, outage);
        });
        
        // Refresh view locally now that we have outages data
        if (!this.isLoading) {
          this.showStationsInView();
        }
      },
      error: (err) => console.error("Error loading outages:", err)
    });
  }

  onMapMoveEnd(): void {
    if (!this.autoLoadOnMove) {
      return;
    }

    this.showStationsInView();
  }

  onAutoLoadChange(): void {
    if (!this.autoLoadOnMove) {
      return;
    }

    this.showStationsInView();
  }

  onStationFilterChange(): void {
    if (!this.map || this.isLoading) {
      return;
    }

    this.showStationsInView();
  }

  showStationsInView(): void {
    if (!this.map || this.isLoading) {
      return;
    }

    const bounds = this.map.getBounds();
    
    this.isLoading = true;
    this.substationsService.isLoading$.next(true);

    this.substationsService
      .getStationsByBounds(
        {
          minLat: bounds.getSouth(),
          maxLat: bounds.getNorth(),
          minLon: bounds.getWest(),
          maxLon: bounds.getEast()
        },
        {
          includeMedium: this.showMediumVoltage,
          includeHigh: this.showHighVoltage,
          includeDT: this.showDistributionTransformers
        }
      )
      .pipe(
        switchMap((stationsResult) => {
          const tsIds = (stationsResult.highVoltage || []).map(s => s.id);
          const ssIds = (stationsResult.mediumVoltage || []).map(s => s.id);
          const dtIds = (stationsResult.distributionTransformers || []).map(s => s.id);

          const requests: any = {
            stations: of(stationsResult)
          };

          if (this.showF33) {
            requests.f33Lines = this.substationsService.getF33Lines({
              tsIds,
              ssIds,
              dtIds,
              showTS: this.showHighVoltage,
              showSS: this.showMediumVoltage,
              showDT: this.showDistributionTransformers
            });
          } else {
            requests.f33Lines = of([]);
          }

          if (this.showF11) {
            requests.f11Lines = this.substationsService.getF11Lines({
              tsIds,
              ssIds,
              dtIds,
              showTS: this.showHighVoltage,
              showSS: this.showMediumVoltage,
              showDT: this.showDistributionTransformers
            });
          } else {
            requests.f11Lines = of([]);
          }

          return forkJoin(requests).pipe(
            map((res: any) => ({
              stations: res.stations,
              f33Lines: res.f33Lines,
              f11Lines: res.f11Lines
            }))
          );
        }),
        finalize(() => {
          this.isLoading = false;
          this.substationsService.isLoading$.next(false);
        })
      )
      .subscribe({
        next: (result) => {
          this.renderStations(
            result.stations.mediumVoltage || [],
            result.stations.highVoltage || [],
            result.stations.distributionTransformers || [],
            result.f33Lines || [],
            result.f11Lines || []
          );
        },
        error: (err) => {
          console.error(err);
          this.addToast('Greska pri ucitavanju podstanica. Proveri da li backend radi na localhost:5067.', 'error');
        }
      });
  }

  showMockStations(): void {
    const mediumVoltage = this.showMediumVoltage ? this.mockMediumVoltage : [];
    const highVoltage = this.showHighVoltage ? this.mockHighVoltage : [];
    const distributionTransformers = this.showDistributionTransformers ? this.mockDistributionTransformers : [];

    this.renderStations(mediumVoltage, highVoltage, distributionTransformers, [], []);

    const counts = [
      this.showMediumVoltage ? 10 : 0,
      this.showHighVoltage ? 10 : 0,
      this.showDistributionTransformers ? 10 : 0
    ];
    const total = counts.reduce((a, b) => a + b, 0);

    this.addToast(`Prikazano je ${total} mock podstanica (SN: ${counts[0]}, VN: ${counts[1]}, DT: ${counts[2]}).`, 'info');
  }

  dismissToast(toastId: number): void {
    this.toasts = this.toasts.filter((toast) => toast.id !== toastId);
  }

  // Add Station Modal Logics
  openAddStationModal(): void {
    this.showAddStationModal = true;
    this.isPickingLocation = false;
    this.newStation = { type: 'TS', name: '', latitude: null, longitude: null, nameplateRating: null };
  }

  closeAddStationModal(): void {
    this.showAddStationModal = false;
  }

  pickLocationOnMap(): void {
    this.showAddStationModal = false;
    this.isPickingLocation = true;
    this.addToast('Klikni bilo gde na mapu da izaberes lokaciju.', 'info');
  }

  saveNewStation(): void {
    if (!this.newStation.name || !this.newStation.latitude || !this.newStation.longitude) {
      this.addToast('Sva osnovna polja moraju biti popunjena!', 'error');
      return;
    }

    const payload: Partial<Station> & { nameplateRating?: number } = {
      name: this.newStation.name,
      latitude: this.newStation.latitude,
      longitude: this.newStation.longitude
    };

    let apiCall: Observable<any>;

    if (this.newStation.type === 'TS') {
      apiCall = this.substationsService.createTransmissionStation(payload);
    } else if (this.newStation.type === 'SS') {
      apiCall = this.substationsService.createSubstation(payload);
    } else {
      payload.nameplateRating = this.newStation.nameplateRating;
      apiCall = this.substationsService.createDistributionSubstation(payload);
    }

    apiCall.subscribe({
      next: (res: any) => {
        this.addToast(`Nova stanica (${this.newStation.name}) uspesno dodata!`, 'success');
        this.closeAddStationModal();
        this.showStationsInView(); // Reload stations to show the new one
      },
      error: (err: any) => {
        this.addToast('Došlo je do greške prilikom čuvanja stanice na server.', 'error');
      }
    });
  }

  private addToast(text: string, type: ToastType): void {
    const toast: ToastMessage = {
      id: Date.now() + Math.floor(Math.random() * 1000),
      text,
      type
    };

    this.toasts = [...this.toasts, toast];
    setTimeout(() => {
      this.dismissToast(toast.id);
    }, 4200);
  }

  private createMarker(station: Station, markerIcon: L.Icon, type: 'TS' | 'SS' | 'DT'): L.Marker {
    const zIndexMap = {
      'TS': 3000,
      'SS': 2000,
      'DT': 1000
    };

    let finalIcon: L.Icon | L.DivIcon = markerIcon;
    const outage = this.outagesMap.get(station.id);
    let popupOutageHTML = '';

    if (outage) {
        const totalIspadi = outage.ispadA + outage.ispadB + outage.ispadC;
        if (totalIspadi > 17) {
            const colorClass = totalIspadi > 100 ? 'critical' : 'warning';
            const iconUrl = markerIcon.options.iconUrl;
            const iconSize = markerIcon.options.iconSize as [number, number];
            const width = iconSize ? iconSize[0] : 32;
            const height = iconSize ? iconSize[1] : 32;
            
            finalIcon = L.divIcon({
              className: '',
              html: `
                <div class="marker-pulse-${colorClass}" style="width: ${width}px; height: ${height}px;">
                  <img src="${iconUrl}" style="width: 100%; height: 100%; object-fit: contain; position: relative; z-index: 10;" />
                </div>
              `,
              iconSize: [width, height],
              iconAnchor: markerIcon.options.iconAnchor,
              popupAnchor: markerIcon.options.popupAnchor
            });

            const popupStatus = totalIspadi > 100 
              ? '<span style="color: #ef4444; font-weight: bold;">🔴 KRITIČNO</span>' 
              : '<span style="color: #f97316; font-weight: bold;">🟠 UPOZORENJE (ISPAD FAZE)</span>';

            popupOutageHTML = `
              <div style="margin-top: 10px; border-top: 1px solid #ccc; padding-top: 10px;">
                <div style="margin-bottom: 8px;">Status: ${popupStatus}</div>
                <table style="width: 100%; font-size: 0.9em; margin-bottom: 10px;">
                  <tr>
                    <td><b>Faza A:</b></td>
                    <td style="color: ${outage.minVoltageA < 100 ? '#ef4444' : '#22c55e'}">${outage.minVoltageA}V</td>
                    <td>(${outage.ispadA} ispada)</td>
                  </tr>
                  <tr>
                    <td><b>Faza B:</b></td>
                    <td style="color: ${outage.minVoltageB < 100 ? '#ef4444' : '#22c55e'}">${outage.minVoltageB}V</td>
                    <td>(${outage.ispadB} ispada)</td>
                  </tr>
                  <tr>
                    <td><b>Faza C:</b></td>
                    <td style="color: ${outage.minVoltageC < 100 ? '#ef4444' : '#22c55e'}">${outage.minVoltageC}V</td>
                    <td>(${outage.ispadC} ispada)</td>
                  </tr>
                </table>
                <div style="font-size: 0.85em; color: #666; text-align: center;">Ukupno ispada: <b>${totalIspadi}</b></div>
              </div>
            `;
        }
    }

    const marker = L.marker([station.latitude, station.longitude], { 
      icon: finalIcon,
      zIndexOffset: zIndexMap[type] || 0
    });
    
    if (type === 'DT') {
      marker.bindPopup(`
        <div style="padding: 10px; min-width: 200px;">
          <h5 style="margin: 0 0 5px 0;">${station.name}</h5>
          <b>Tip stanice:</b> Distributivna Trafo-Stanica (DT)<br/>
          ${popupOutageHTML || '<i>Nema prijavljenih ispada faza (ili parametri su u granicama normale).</i>'}
        </div>
      `);
      return marker;
    }

    // Za TS i SS prvenstveno postavljamo početni tekst/loader

    marker.bindPopup(`<div style="padding: 10px;">Učitavanje podataka... <br><small>(${station.name})</small></div>`);
    
    // Prilikom POKRETANJA popup prozora preuzimamo podatke kako bi radilo na svaki klik
    marker.on('popupopen', () => {
      marker.setPopupContent(`<div style="padding: 10px;">Učitavanje podataka... <br><small>(${station.name})</small></div>`);

      const details$ = type === 'TS' ? this.substationsService.getTsDetails(station.id) : this.substationsService.getSsDetails(station.id);
      const feeders$ = type === 'TS' ? this.substationsService.getTsFeeders(station.id, this.showF33, this.showF11) : this.substationsService.getSsFeeders(station.id);

      forkJoin({ details: details$, feeders: feeders$ }).subscribe({
        next: ({details, feeders}) => {
          this.buildPopupContent(marker, details, feeders, type);
        },
        error: () => {
          marker.setPopupContent(`<div style="padding: 10px; color: red;">Greška pri učitavanju detalja za ${station.name}.</div>`);
        }
      });
    });

    return marker;
  }

  private buildPopupContent(marker: L.Marker, details: StationDetailsDto, feeders: FeederLineWithLengthDto[], type: 'TS' | 'SS'): void {
    const isTS = type === 'TS';
    const typeLabel = isTS ? 'Visokonaponska (TS)' : 'Srednjenaponska (SS)';
    
    const avgLength = feeders.length > 0
        ? (feeders.reduce((sum, f) => sum + f.averageLengthKm, 0) / feeders.length).toFixed(2)
        : '0.00';

    const container = document.createElement('div');
    let outageHTML = '';
    const outage = this.outagesMap.get(details.id);
    if (outage) {
        const tI = outage.ispadA + outage.ispadB + outage.ispadC;
        if (tI > 17) {
            outageHTML = `
              <div style="margin-top: 10px; margin-bottom: 10px; border-top: 1px solid #ccc; border-bottom: 1px solid #ccc; padding: 10px 0;">
                <div style="color: ${tI > 100 ? '#ef4444' : '#f97316'}; font-weight: bold; margin-bottom: 5px;">
                  ${tI > 100 ? '🔴 KRITIČNO' : '🟠 UPOZORENJE (ISPAD FAZE)'}
                </div>
                Ukupno ispada: <b>${tI}</b><br/>
              </div>
            `;
        }
    }

    container.innerHTML = `
      <div style="padding: 5px 10px; min-width: 220px;">
        <h6 style="margin: 0 0 10px 0; font-weight: bold; font-size: 14px; border-bottom: 1px solid #ccc; padding-bottom: 5px;">${details.name}</h6>
        <div style="margin-bottom: 10px; font-size: 13px;">
          <b>Tip:</b> ${typeLabel}<br/>
          ${isTS ? `<b>Povezane SS:</b> ${details.connectedSsCount}<br/>` : ''}
          <b>Povezane DT:</b> ${details.connectedDtCount}<br/>
          <b>Broj vodova:</b> ${feeders.length}<br/>
          <b>Prosečna dužina:</b> ${avgLength} km
        </div>
        ${outageHTML}
        <button class="btn btn-sm btn-primary w-100 mb-2 popup-draw-lines">Prikaži vodove</button>
        <button class="btn btn-sm btn-secondary w-100 popup-draw-endpoints">Prikaži krajnje stanice</button>
      </div>
    `;

    const drawLinesBtn = container.querySelector('.popup-draw-lines');
    if (drawLinesBtn) {
      drawLinesBtn.addEventListener('click', () => {
        this.drawSpecialFeeders(feeders);
      });
    }

    const drawEndpointsBtn = container.querySelector('.popup-draw-endpoints');
    if (drawEndpointsBtn) {
      drawEndpointsBtn.addEventListener('click', () => {
        this.drawEndStations(feeders);
      });
    }

    marker.setPopupContent(container);
  }

  private drawSpecialFeeders(feeders: FeederLineWithLengthDto[]): void {
    this.stationLinesLayer.clearLayers();
    
    if (feeders.length === 0) {
      this.addToast('Nema pronađenih vodova za ovu stanicu.', 'info');
      return;
    }

    feeders.forEach(line => {
      const color = line.feederType === 'F33' ? '#ff4444' : '#4444ff';
      const pl = L.polyline(
        [
          [line.sourceLat, line.sourceLon],
          [line.targetLat, line.targetLon]
        ],
        { color: color, weight: 6, opacity: 1, dashArray: '8, 8' } // Deblja linija sa prekidima da se razlikuje
      ).bindPopup(`
        <div style="padding: 5px;">
          <b>${line.feederName}</b><br/>
          Mreža: ${line.feederType}<br/>
          Izračunata udaljenost: <b>${line.averageLengthKm.toFixed(2)} km</b>
        </div>
      `);
      
      this.stationLinesLayer.addLayer(pl);
    });

    if (this.map && !this.map.hasLayer(this.stationLinesLayer)) {
      this.map.addLayer(this.stationLinesLayer);
    }
    
    this.addToast(`Nacrtano ${feeders.length} vodova.`, 'success');
  }

  private drawEndStations(feeders: FeederLineWithLengthDto[]): void {
    this.endStationsLayer.clearLayers();

    if (feeders.length === 0) {
      this.addToast('Nema krajnjih stanica za prikaz.', 'info');
      return;
    }

    feeders.forEach(line => {
      const color = line.feederType === 'F33' ? '#ff4444' : '#4444ff';
      const cm = L.circleMarker([line.targetLat, line.targetLon], {
        radius: 6,
        color: 'black',
        weight: 1,
        fillColor: color,
        fillOpacity: 1
      }).bindPopup(`<b>Krajnja stanica</b><br>Vod: ${line.feederName}`);

      this.endStationsLayer.addLayer(cm);
    });

    if (this.map && !this.map.hasLayer(this.endStationsLayer)) {
      this.map.addLayer(this.endStationsLayer);
    }

    this.addToast(`Prikazano ${feeders.length} krajnjih stanica.`, 'success');
  }

  private renderStations(
    mediumVoltage: Station[],
    highVoltage: Station[],
    distributionTransformers: Station[],
    f33Lines: FeederLine[],
    f11Lines: FeederLine[]
  ): void {
    // Brisanje starih analiziranih linija ukoliko se renderuje nova tura
    this.stationLinesLayer.clearLayers();
    this.endStationsLayer.clearLayers();

    const mediumVoltageMarkers = this.showMediumVoltage
      ? mediumVoltage.map((station) => this.createMarker(station, this.mediumVoltageIcon, 'SS'))
      : [];
    const highVoltageMarkers = this.showHighVoltage
      ? highVoltage.map((station) => this.createMarker(station, this.highVoltageIcon, 'TS'))
      : [];
    const distributionTransformerMarkers = this.showDistributionTransformers
      ? distributionTransformers.map((station) => this.createMarker(station, this.distributionTransformerIcon, 'DT'))
      : [];
    
    const allMarkers = [
      ...mediumVoltageMarkers,
      ...highVoltageMarkers,
      ...distributionTransformerMarkers
    ];

    const f33Polylines = f33Lines.map(line => {
      return L.polyline(
        [
          [line.sourceLat, line.sourceLon],
          [line.targetLat, line.targetLon]
        ],
        { color: 'red', weight: 4, opacity: 0.8 }
      ).bindPopup(`<b>${line.feederName}</b><br>Vrsta: ${line.feederType}<br>Izvor: ${line.sourceStationName}<br>Odrediste: ${line.targetStationName}`);
    });

    const f11Polylines = f11Lines.map(line => {
      return L.polyline(
        [
          [line.sourceLat, line.sourceLon],
          [line.targetLat, line.targetLon]
        ],
        { color: 'blue', weight: 3, opacity: 0.8 }
      ).bindPopup(`<b>${line.feederName}</b><br>Vrsta: ${line.feederType}<br>Izvor: ${line.sourceStationName}<br>Odrediste: ${line.targetStationName}`);
    });

    let containerLayer: L.Layer;

    if (this.useClustering) {
      const markerCluster = L.markerClusterGroup({
        maxClusterRadius: 45,
        showCoverageOnHover: false,
        spiderfyOnMaxZoom: true
      });
      markerCluster.addLayers(allMarkers);
      containerLayer = markerCluster;
    } else {
      containerLayer = L.layerGroup(allMarkers);
    }

    const linesLayer = L.layerGroup([...f33Polylines, ...f11Polylines]);

    this.layers = [
      this.baseLayer,
      linesLayer,
      containerLayer,
      this.stationLinesLayer,
      this.endStationsLayer
    ];

    const total = allMarkers.length;
    const totalLines = f33Polylines.length + f11Polylines.length;

    if (total === 0 && totalLines === 0) {
      this.addToast('Nema podstanica i vodova u trenutnom prikazu mape.', 'info');
      return;
    }

    this.addToast(
      `Ucitano ${total} podstanica i ${totalLines} vodova.`,
      'success'
    );
  }

}
