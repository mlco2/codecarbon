import { Routes } from '@angular/router';
import { LoginPageComponent } from './login-page/login-page.component';
import { OrgPageComponent } from './org-page/org-page.component';

export const routes: Routes = [
     { path: "login", component: LoginPageComponent },
     { path: "web/login", component: LoginPageComponent },
     { path: "orgs", component: OrgPageComponent },
];
