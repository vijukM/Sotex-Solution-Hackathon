import { Component, OnInit, AfterViewInit } from '@angular/core';
import { ChartConfiguration, ChartData, ChartType } from 'chart.js';
import { forkJoin, switchMap } from 'rxjs';
import { SubstationsService, Station, FeederLine } from '../../services/substations.service';
import * as L from 'leaflet';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit, AfterViewInit {
  isLoading = true;
  private miniMap: L.Map | undefined;

  // KPI Metrics
  totalTs = 0;
  totalSs = 0;
  totalDs = 0;
  totalF33 = 0;
  totalF11 = 0;
  
  dsWithF11 = 0;
  dsWithF33 = 0;

  percF11 = 0;
  percF33 = 0;

  // Derived Data
  isolatedStations: string[] = [];
  top5SsByDsMap: { name: string, count: number }[] = [];
  tsSsConnections: { tsName: string; ssName: string; f33Name: string }[] = [];

  // Charts
  // 1. Station distribution pie chart
  public pieChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'right',
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            let label = context.label || '';
            if (label) {
              label += ': ';
            }
            if (context.parsed !== null) {
              const dataset = context.chart.data.datasets[0];
              const total = (dataset.data as number[]).reduce((a, b) => a + b, 0);
              const percentage = ((context.parsed / total) * 100).toFixed(1) + '%';
              label += context.parsed + ' (' + percentage + ')';
            }
            return label;
          }
        }
      }
    }
  };
  public pieChartData: ChartData<'pie', number[], string | string[]> = {
    labels: ['Viskokonaponske', 'Srednjenaponske', 'Distribucijske'],
    datasets: [{ data: [0, 0, 0], backgroundColor: ['#0f62fe', '#2cd16e', '#ff4e42'] }]
  };
  public pieChartType: ChartType = 'pie';

  // DS Connection Pie Chart
  public dsPieChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'right',
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            let label = context.label || '';
            if (label) { label += ': '; }
            if (context.parsed !== null) {
              const dataset = context.chart.data.datasets[0];
              const total = (dataset.data as number[]).reduce((a, b) => a + b, 0);
              const percentage = ((context.parsed / total) * 100).toFixed(1) + '%';
              label += context.parsed + ' (' + percentage + ')';
            }
            return label;
          }
        }
      }
    }
  };
  public dsPieChartData: ChartData<'pie', number[], string | string[]> = {
    labels: ['Povezano na F11 (SS)', 'Povezano na F33 (TS)'],
    datasets: [{ data: [0, 0], backgroundColor: ['#8a2be2', '#38b2ce'] }]
  };
  public dsPieChartType: ChartType = 'pie';

  // 2. Bar chart for Top Connections
  public barChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: { beginAtZero: true }
    }
  };
  public barChartType: ChartType = 'bar';
  public barChartData: ChartData<'bar'> = {
    labels: [],
    datasets: [
      { data: [], label: 'Broj povezanih DS-a', backgroundColor: '#0f62fe' }
    ]
  };

  // Trend Chart (Line)
  public trendChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: { display: true, position: 'top' },
      tooltip: {
        callbacks: {
          label: (context) => `${context.dataset.label}: ${context.parsed.y} ispada`
        }
      }
    },
    scales: {
      x: { title: { display: true, text: 'Nedelja (Jan - Apr 2026)' } },
      y: { beginAtZero: true, title: { display: true, text: 'Broj ispada (< 100V)' } }
    }
  };
  public trendChartType: ChartType = 'line';
  public trendChartData: ChartData<'line'> = {
    labels: ['Ned 1', 'Ned 2', 'Ned 3', 'Ned 4', 'Ned 5', 'Ned 6', 'Ned 7', 'Ned 8', 'Ned 9', 'Ned 10', 'Ned 11', 'Ned 12'],
    datasets: [
      {
        label: 'Faza A',
        data: [12, 9, 15, 8, 4, 10, 14, 5, 2, 4, 1, 0],
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        fill: true
      },
      {
        label: 'Faza B',
        data: [5, 2, 0, 1, 19, 24, 12, 6, 0, 0, 0, 3],
        borderColor: '#22c55e',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        tension: 0.4,
        fill: true
      },
      {
        label: 'Faza C',
        data: [85, 92, 105, 110, 124, 131, 98, 85, 76, 68, 53, 40],
        borderColor: '#f97316',
        backgroundColor: 'rgba(249, 115, 22, 0.1)',
        tension: 0.4,
        fill: true
      }
    ]
  };

  // Top 5 Meters Trend Chart
  public meterTrendChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { display: true, position: 'bottom' },
      tooltip: {
        callbacks: {
          label: (context) => `${context.dataset.label}: ${context.parsed.y} kvarova`
        }
      }
    },
    scales: {
      x: { title: { display: false } },
      y: { beginAtZero: true, title: { display: true, text: 'Broj kvarova / ispada' } }
    }
  };
  public meterTrendChartType: ChartType = 'line';
  public meterTrendChartData: ChartData<'line'> = {
    labels: ['Jan (5.)', 'Jan (12.)', 'Jan (19.)', 'Jan (26.)', 'Feb (2.)', 'Feb (9.)', 'Feb (16.)', 'Feb (23.)', 'Mar (2.)', 'Mar (9.)', 'Mar (16.)', 'Mar (23.)'],
    datasets: [
      { label: 'BRIA STREET', data: [15, 12, 14, 18, 20, 25, 22, 19, 15, 10, 8, 5], borderColor: '#ef4444', backgroundColor: 'transparent', borderDash: [5, 5], tension: 0.1, borderWidth: 3, pointRadius: 4, pointBackgroundColor: '#ef4444' },
      { label: 'EFAB QUEEN S/S 4', data: [5, 8, 12, 15, 22, 28, 24, 20, 16, 12, 6, 4], borderColor: '#f97316', backgroundColor: 'transparent', tension: 0.1, borderWidth: 2 },
      { label: 'Nigerian Finance Bldg', data: [8, 10, 11, 14, 18, 15, 12, 9, 7, 5, 2, 0], borderColor: '#eab308', backgroundColor: 'transparent', tension: 0.1, borderWidth: 2 },
      { label: 'BUA COURT DT', data: [12, 15, 10, 8, 5, 4, 3, 3, 2, 1, 0, 0], borderColor: '#3b82f6', backgroundColor: 'transparent', tension: 0.1, borderWidth: 2 },
      { label: 'NO 12 PARAKOU ST', data: [2, 3, 5, 8, 12, 15, 10, 8, 5, 4, 2, 1], borderColor: '#8b5cf6', backgroundColor: 'transparent', tension: 0.1, borderWidth: 2 }
    ]
  };

  constructor(private readonly substationsService: SubstationsService) {}

  ngOnInit(): void {
    this.loadData();
  }

  ngAfterViewInit(): void {
    // Map is initiated in loadData
  }

  private initMap(): void {
    setTimeout(() => {
      const mapContainer = document.getElementById('mini-map');
      if (mapContainer && !this.miniMap) {
        this.miniMap = L.map('mini-map', {
          zoomControl: false,
          attributionControl: false
        }).setView([9.0765, 7.3986], 6); // Uvecaj zoom na celu Nigeriju (zoom 6)
  
        L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
          subdomains: 'abcd',
          maxZoom: 19
        }).addTo(this.miniMap);

        this.substationsService.getStationsByBounds(
          { minLat: 2.0, maxLat: 15.0, minLon: 2.0, maxLon: 15.0 }, // Sira granica
          { includeHigh: true, includeMedium: true, includeDT: false } // Iskljucujemo DT zbog ogromnog broja!
        ).subscribe(data => {
          if (!this.miniMap) return;

          (data.highVoltage || []).forEach(s => {
            if (s.latitude && s.longitude) {
              L.circleMarker([s.latitude, s.longitude], { color: '#0f62fe', radius: 4, weight: 1, fillOpacity: 0.8 }).addTo(this.miniMap!);
            }
          });
          (data.mediumVoltage || []).forEach(s => {
            if (s.latitude && s.longitude) {
              L.circleMarker([s.latitude, s.longitude], { color: '#2cd16e', radius: 3, weight: 1, fillOpacity: 0.7 }).addTo(this.miniMap!);
            }
          });
        });
        
        setTimeout(() => {
          this.miniMap?.invalidateSize();
        }, 500);
      } else if (this.miniMap) {
        this.miniMap.invalidateSize();
      }
    }, 500); // Sacekaj 500ms da se izrenda DOM
  }

  private loadData(): void {
    this.substationsService.getDashboardSummary().subscribe(res => {
      this.totalTs = res.totalTs;
      this.totalSs = res.totalSs;
      this.totalDs = res.totalDs;
      this.totalF33 = res.totalF33;
      this.totalF11 = res.totalF11;
      
      this.dsWithF11 = res.dsWithF11 || 0;
      this.dsWithF33 = res.dsWithF33 || 0;
      this.percF11 = this.totalDs ? Math.round((this.dsWithF11 / this.totalDs) * 100) : 0;
      this.percF33 = this.totalDs ? Math.round((this.dsWithF33 / this.totalDs) * 100) : 0;

      this.tsSsConnections = res.tsSsConnections || [];
      this.top5SsByDsMap = res.top5Ss;
      // You can implement custom logic or extend the API for isolated stations
      this.isolatedStations = res.isolatedStations || []; 

      this.pieChartData.datasets[0].data = [this.totalTs, this.totalSs, this.totalDs];
      this.dsPieChartData.datasets[0].data = [this.dsWithF11, this.dsWithF33];
      
      this.barChartData.labels = this.top5SsByDsMap.map(x => x.name);
      this.barChartData.datasets[0].data = this.top5SsByDsMap.map(x => x.count);

      this.isLoading = false;
      this.initMap();
    });
  }
}



