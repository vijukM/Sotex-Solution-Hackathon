import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AlertsComponent } from './pages/alerts/alerts.component';
import { AnalyticsComponent } from './pages/analytics/analytics.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { MapViewComponent } from './pages/map-view/map-view.component';

const routes: Routes = [
  { path: '', redirectTo: 'map', pathMatch: 'full' },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'map', component: MapViewComponent },
  { path: 'analytics', component: AnalyticsComponent },
  { path: 'alerts', component: AlertsComponent },
  { path: '**', redirectTo: 'map' }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
