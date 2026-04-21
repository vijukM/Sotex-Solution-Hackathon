import { Component } from '@angular/core';
import { NavigationEnd, Router } from '@angular/router';
import { filter } from 'rxjs/operators';
import { SubstationsService, MapFilters } from './services/substations.service';

interface NavItem {
  label: string;
  route: string;
}

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  navItems: NavItem[] = [
    { label: 'Dashboard', route: '/dashboard' },
    { label: 'Analytics', route: '/analytics' },
    { label: 'Alerts', route: '/alerts' }
  ];

  isMapRoute = false;
  showMapMenu = false;
  isLoading = false;
  isZoomTooLowForUnclustered = false;
  filters: MapFilters = { showSN: true, showVN: true, showDT: true, autoLoad: false, useClustering: true, showF33: false, showF11: false };

  constructor(
    private router: Router,
    public substationsService: SubstationsService
  ) {
    this.router.events
      .pipe(filter((event) => event instanceof NavigationEnd))
      .subscribe((event: any) => {
        this.isMapRoute = event.urlAfterRedirects.includes('/map');
      });

    this.substationsService.filters$.subscribe(f => {
      this.filters = f;
    });

    this.substationsService.isLoading$.subscribe(loading => {
      this.isLoading = loading;
    });

    this.substationsService.mapZoom$.subscribe(zoom => {
      // Disable allowing unclustered markers if zoom level is 10 or less
      this.isZoomTooLowForUnclustered = zoom <= 10;
      if (this.isZoomTooLowForUnclustered && !this.filters.useClustering) {
        this.filters.useClustering = true;
        this.onFilterChange();
      }
    });
  }

  toggleMapMenu(event?: Event) {
    if (event) {
      event.stopPropagation();
    }
    this.showMapMenu = !this.showMapMenu;
  }

  onFilterChange() {
    // Ako nisu ispunjeni uslovi za F33 (mora VN i barem jos jedan tip - SN ili DT), onda iskljucujemo
    if (!(this.filters.showVN && (this.filters.showSN || this.filters.showDT))) {
      this.filters.showF33 = false;
    }
    // Ako nisu ispunjeni uslovi za F11 (mora DT i barem jos jedan tip - VN ili SN), onda iskljucujemo
    if (!(this.filters.showDT && (this.filters.showVN || this.filters.showSN))) {
      this.filters.showF11 = false;
    }

    this.substationsService.filters$.next({ ...this.filters });
    // this.substationsService.triggerFetch$.next(); <-- Uklonjeno automatsko ucitavanje na promenu checkbox-a
  }

  triggerFetch() {
    this.substationsService.triggerFetch$.next();
    this.showMapMenu = false; // Hide menu after fetch
  }
}
