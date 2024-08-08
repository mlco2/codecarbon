import { Component } from '@angular/core';
import { CarbonApiService } from '../carbon-api.service';

@Component({
  selector: 'app-top-bar',
  standalone: true,
  imports: [],
  templateUrl: './top-bar.component.html',
  styleUrl: './top-bar.component.scss'
})
export class TopBarComponent {
  constructor(public api: CarbonApiService) {
    
  }
}
