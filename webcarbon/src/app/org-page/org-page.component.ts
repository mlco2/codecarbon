import { Component, OnInit } from '@angular/core';
import { CarbonApiService } from '../carbon-api.service';

@Component({
  selector: 'app-org-page',
  standalone: true,
  imports: [],
  templateUrl: './org-page.component.html',
  styleUrl: './org-page.component.scss'
})
export class OrgPageComponent implements OnInit {
  public orgs: any = [];
  public status: any = '';
  constructor(public api: CarbonApiService) {

  }

  async ngOnInit() {
    this.orgs = await this.api.get("organizations");
    this.status = await this.api.get("protected2");
    const user = await this.api.get("user2");
    console.log({user});



    const user3 = await this.api.get("user3");
    console.log({user3});    
  }
}
