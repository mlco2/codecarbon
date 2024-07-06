import { Injectable } from '@angular/core';
import { jwtDecode } from "jwt-decode";

const apiUrl = "https://codecarbon.server";

@Injectable({
  providedIn: 'root'
})
export class CarbonApiService {
  private creds: {access_token:string, id_token:string} | null= null;
  public email: string|null = "";

  constructor() {
    try {
      const creds: any = this.loadCreds();
      console.log("()", creds)
      this.setCreds(JSON.parse(atob(creds)));
    } catch(e) {
    }
  }

  public async listOrganizations() {
    const result = await (await fetch(`${apiUrl}/organizations`)).json();
    console.log(result);
    return result;
  }

  public setCreds(creds: {access_token:string, id_token:string}) {
    this.creds = creds;
    const id_token: any = jwtDecode(creds.id_token);
    this.email = id_token?.email;
    console.log({id_token})
  }

  public saveCreds(creds: string) {
    localStorage.setItem("creds", creds);
  }

  public loadCreds() {
    const creds_string = localStorage.getItem("creds");
    return creds_string;
  }  

  public async get(path: string) {
    const result = await (await fetch(`${apiUrl}/${path}`, {
      method: "GET", // *GET, POST, PUT, DELETE, etc.
      cache: "no-cache", // *default, no-cache, reload, force-cache, only-if-cached
      headers: {
        Authorization: `Bearer ${this.creds?.access_token}`,
      },
    })).json();
    console.log(result);
    return result;
  }

  public async testLogin() {
    const response = await fetch(`${apiUrl}/protected`);
    const redirected = response.redirected;
    
    if (redirected) {
      return {
        "status":"redirect", 
        "url": response.url.replaceAll("http", "https").replace("httpss", "https")
    };
    }
    const result = await response.json();
    console.log({result, redirected});
    return result;
  }  
}
