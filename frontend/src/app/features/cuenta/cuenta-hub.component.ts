import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-cuenta-hub',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './cuenta-hub.component.html',
  styleUrl: './cuenta-hub.component.css',
})
export class CuentaHubComponent {}
