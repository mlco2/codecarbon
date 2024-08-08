import { CarbonApiService } from '../carbon-api.service';
import { ActivatedRoute } from '@angular/router';
import { Component, OnInit, inject } from '@angular/core';

@Component({
  selector: 'app-login-page',
  standalone: true,
  imports: [],
  templateUrl: './login-page.component.html',
  styleUrl: './login-page.component.scss'
})
export class LoginPageComponent implements OnInit {
  public orgs: any[] = [];
  public loginTest: any = '';
  //private route = inject(ActivatedRoute);

  constructor(public api: CarbonApiService, private route: ActivatedRoute) {
    console.log("carbonapi()");
    console.log(route);
    this.init();

  }

  public async init() {
    this.orgs = await this.api.listOrganizations();

    this.loginTest = "...";
    this.loginTest = await this.api.testLogin();

    console.log({orgs:this.orgs});
  }

  ngOnInit() {
    this.route.paramMap.subscribe((params) => {
      //this.productId = params.get('productId')!;
      console.log(params);

      const creds = this.route.snapshot.queryParamMap.get('creds');
      console.log(creds);  

      console.log(this.route.snapshot.url);

      try {
        const creds_64 = window.location.hash.split("=")[1];
        //const creds = Buffer.from(creds_64, 'base64');
        const creds = JSON.parse(atob(creds_64));
        console.log({creds});
        this.api.setCreds(creds);
        this.api.saveCreds(creds_64);
      } catch(e) {

      }
    });    
  }


}
