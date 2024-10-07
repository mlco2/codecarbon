#!/usr/bin/env python3
import dataclasses
import os
import re
import secrets
import typer
import subprocess
from typing_extensions import Annotated

app = typer.Typer()

@dataclasses.dataclass
class Settings:
    run_traefik: bool = True
    run_fief: bool = True
    fief_hostname: str = "fief.localhost"
    hostname: str = "codecarbon.localhost"
    admin_email: str = "admin@localhost"


def replace(source, destination, variables):
    with open(source) as f:
        with open(destination, 'w') as f_out:
            for line in f.readlines():
                for k,v in variables.items():
                    if re.match(f"^{k}=.*", line):
                        line = f"{k}={v}\n"
                        continue
                f_out.write(line)


def _setup(settings: Settings):
    print("="*40)
    print("Settings:")
    print("="*40)
    for k,v in settings.__dict__.items():
        print(f"{k:>{20}}: {v}")

    variables = {
        "HOSTNAME": settings.hostname,
        "APP_HOSTNAME": settings.hostname,        
        "AUTH_HOSTNAME": settings.fief_hostname,
        "FIEF_HOSTNAME": settings.fief_hostname,
        "FIEF_DOMAIN": settings.fief_hostname,
        "ADMIN_EMAIL": settings.admin_email,
        "FRONTEND_URL": f"https://{settings.hostname}",
        "FIEF_URL": f"https://{settings.fief_hostname}",
        "JWT_KEY": secrets.token_urlsafe(32),
    }
    if settings.run_fief:
        variables["FIEF_CLIENT_ID"] = secrets.token_urlsafe(32)
        variables["FIEF_CLIENT_SECRET"] = secrets.token_urlsafe(64)
        replace("./deploy/.env.fief.example", "./deploy/.env.fief", {
            **variables,
            "SECRET": secrets.token_urlsafe(64),
            "DATABASE_PASSWORD": secrets.token_urlsafe(32),
        })
        
    replace("./deploy/.env.example", ".env", {
        **variables,
        })
    replace("./deploy/.env.example", "./deploy/.env", {
        **variables,
        })
    replace("./deploy/env.webapp.example", "webapp/.env.development", {
        **variables,
        "NEXT_PUBLIC_BASE_URL": f"https://{settings.hostname}",
        "NEXT_PUBLIC_API_URL": f"https://{settings.hostname}/api",
        "FIEF_BASE_URL": variables["FIEF_URL"]
        })
    
    print("To start:")
    print("./deploy/deploy.py start " \
          + (" --traefik" if settings.run_traefik else "") \
          + (" --fief" if settings.run_fief else "") \
          + " --codecarbon"
          )

@app.command()
def start(traefik: Annotated[bool, typer.Option()] = False,
          fief: Annotated[bool, typer.Option()] = False,
          codecarbon: Annotated[bool, typer.Option()] = False,
          ):
    subprocess.check_output(["docker", "network", "create", "shared"])
    if traefik:
        res = subprocess.check_output([
            "docker-compose",
            "-p","traefik",
            "-f", "traefik-compose.yml",
            "up", "-d",
        ], cwd="./deploy")
    if fief:
        subprocess.check_output([
            "docker-compose",
            "-p","fief",
            "-f", "fief-compose.yml",
            "up", "-d",
        ], cwd="./deploy")
    if codecarbon:
        subprocess.check_output([
            "docker-compose",
            "-p","codecarbon",
            "-f", "docker-compose.yml",
            "up", "-d",
        ], cwd="./")

@app.command()
def setup():
    print(f"This will setup local docker compose files.")
    settings = Settings()
    if input("Do you want to setup and run the default configuration ? y/n [y]").lower().strip() or "y" == "y":
        _setup(settings)
        return

    settings.run_traefik = input("Do you want to setup traefik ? y/n [y]").lower().strip() != "n"
    settings.run_fief = input("Do you want to setup fief (auth server) ? y/n [y]").lower().strip() != "n"
    if settings.run_fief:
        settings.fief_hostname = input("Enter the hostname of fief (auth server). [fief.localhost]").strip() or "fief.localhost"
    settings.hostname = input("Enter the hostname for codecarbon. [codecarbon.localhost]").strip() or "codecarbon.localhost"


if __name__ == "__main__":
    app()
