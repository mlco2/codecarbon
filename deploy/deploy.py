#!/usr/bin/env python3
import dataclasses
import os
import re
import secrets
import typer
import subprocess
from typing_extensions import Annotated
from pydantic_settings import BaseSettings, SettingsConfigDict


# TODO: use pydantic settings
class FiefSettings(BaseSettings):
    fief_main_admin_api_key: str
    model_config = SettingsConfigDict(
        env_file="deploy/.env.fief", env_file_encoding="utf-8", extra="allow"
    )


app = typer.Typer()


@dataclasses.dataclass
class Settings:
    run_traefik: bool = True
    run_fief: bool = True
    fief_hostname: str = "fief.localhost"
    hostname: str = "codecarbon.localhost"
    admin_email: str = "admin@localhost"
    fief_admin_password: str = secrets.token_urlsafe(20)


def replace(source, destination, variables):
    with open(source) as f:
        with open(destination, "w") as f_out:
            for line in f.readlines():
                for k, v in variables.items():
                    if re.match(f"^{k}=.*", line):
                        line = f"{k}={v}\n"
                        continue
                f_out.write(line)


def _setup(settings: Settings):
    print("=" * 40)
    print("Settings:")
    print("=" * 40)
    for k, v in settings.__dict__.items():
        print(f"{k:>{20}}: {v}")

    variables = {
        "HOSTNAME": settings.hostname,
        "APP_HOSTNAME": settings.hostname,
        "AUTH_HOSTNAME": settings.fief_hostname,
        "FIEF_HOSTNAME": settings.fief_hostname,
        "FIEF_DOMAIN": settings.fief_hostname,
        "FIEF_MAIN_USER_PASSWORD": settings.fief_admin_password,
        "ADMIN_EMAIL": settings.admin_email,
        "FRONTEND_URL": f"https://{settings.hostname}",
        "FIEF_URL": f"https://{settings.fief_hostname}",
        "JWT_KEY": secrets.token_urlsafe(32),
    }
    if settings.run_fief:
        variables["FIEF_CLIENT_ID"] = secrets.token_urlsafe(32)
        variables["FIEF_CLIENT_SECRET"] = secrets.token_urlsafe(64)
        db_password = secrets.token_urlsafe(32)
        replace(
            "./deploy/.env.fief.example",
            "./deploy/.env.fief",
            {
                **variables,
                "FIEF_MAIN_ADMIN_API_KEY": secrets.token_urlsafe(64),
                "SECRET": secrets.token_urlsafe(64),
                "DATABASE_PASSWORD": db_password,
                "POSTGRES_PASSWORD": db_password,
            },
        )

    replace(
        "./deploy/.env.example",
        ".env",
        {
            **variables,
        },
    )
    replace(
        "./deploy/.env.example",
        "./deploy/.env",
        {
            **variables,
        },
    )
    replace(
        "./deploy/env.webapp.example",
        "webapp/.env.development",
        {
            **variables,
            "NEXT_PUBLIC_BASE_URL": f"https://{settings.hostname}",
            "NEXT_PUBLIC_API_URL": f"https://{settings.hostname}/api",
            "FIEF_BASE_URL": variables["FIEF_URL"],
        },
    )

    print(
        f"""
Useful informations:
Fief admin username: admin@mydomain.com
Fief admin password: {settings.fief_admin_password}
    """
    )

    print("To start:")
    print(
        "./deploy/deploy.py start "
        + (" --traefik" if settings.run_traefik else "")
        + (" --fief" if settings.run_fief else "")
        + " --codecarbon"
    )


@app.command()
def wipe():
    """
    This will remove all containers, data volumes and images
    This will not remove data on local folders
    """
    subprocess.check_output(["docker-compose", "-p", "codecarbon", "stop"], cwd="./")
    subprocess.check_output(
        ["docker-compose", "-p", "codecarbon", "rm", "-v", "-f"], cwd="./"
    )
    subprocess.check_output(
        ["docker-compose", "-p", "fief", "-f", "fief-compose.yml", "stop"],
        cwd="./deploy",
    )
    subprocess.check_output(
        ["docker-compose", "-p", "fief", "-f", "fief-compose.yml", "rm", "-v", "-f"],
        cwd="./deploy",
    )
    subprocess.check_output(
        ["docker-compose", "-p", "traefik", "-f", "traefik-compose.yml", "stop"],
        cwd="./deploy",
    )
    subprocess.check_output(
        [
            "docker-compose",
            "-p",
            "traefik",
            "-f",
            "traefik-compose.yml",
            "rm",
            "-v",
            "-f",
        ],
        cwd="./deploy",
    )
    subprocess.check_output(
        [
            "docker-compose",
            "-p",
            "traefik",
            "-f",
            "traefik-compose.yml",
            "rm",
            "-v",
            "-f",
        ],
        cwd="./deploy",
    )
    subprocess.check_output(
        [
            "docker",
            "volume",
            "rm",
            "pgadmin_codecarbon_data1",
            "postgres_codecarbon_data1",
            "postgres_fief_data",
            "redis_data",
            "letsencrypt_data",
        ]
    )


def configure_fief():
    fief_settings = FiefSettings()
    import requests

    api = requests.Session()
    api.headers["Authorization"] = f"Bearer {fief_settings.fief_main_admin_api_key}"
    url = "https://fief.localhost/admin/api"
    clients = api.get(url + "/clients", verify=False)


@app.command()
def start(
    traefik: Annotated[bool, typer.Option()] = False,
    fief: Annotated[bool, typer.Option()] = False,
    codecarbon: Annotated[bool, typer.Option()] = False,
):
    try:
        subprocess.check_output(["docker", "network", "create", "shared"])
    except:
        ...

    if traefik:
        print("Starting traefik")
        res = subprocess.check_output(
            [
                "docker-compose",
                "-p",
                "traefik",
                "-f",
                "traefik-compose.yml",
                "up",
                "-d",
            ],
            cwd="./deploy",
        )
    if fief:
        print("Starting fief")
        subprocess.check_output(
            [
                "docker-compose",
                "-p",
                "fief",
                "-f",
                "fief-compose.yml",
                "up",
                "-d",
            ],
            cwd="./deploy",
        )
        print("Configuring fief")
        configure_fief()
    if codecarbon:
        subprocess.check_output(
            [
                "docker-compose",
                "-p",
                "codecarbon",
                "-f",
                "docker-compose.yml",
                "up",
                "-d",
            ],
            cwd="./",
        )

    print(
        f"""
=========================================
Your codecarbon server is now running !
You can access it:
https://codecarbon.localhost
"""
    )
    if fief:
        print(
            """
The fief server is running:
https://fief.localhost
"""
        )
    print(
        """
You can run the webapp locally for local development on the port 3000 and access it:
https://webapp.localhost          
          """
    )


@app.command()
def setup():
    print(f"This will setup local docker compose files.")
    settings = Settings()
    if (
        input("Do you want to setup and run the default configuration ? y/n [y]")
        .lower()
        .strip()
        or "y" == "y"
    ):
        _setup(settings)
        return

    settings.run_traefik = (
        input("Do you want to setup traefik ? y/n [y]").lower().strip() != "n"
    )
    settings.run_fief = (
        input("Do you want to setup fief (auth server) ? y/n [y]").lower().strip()
        != "n"
    )
    if settings.run_fief:
        settings.fief_hostname = (
            input("Enter the hostname of fief (auth server). [fief.localhost]").strip()
            or "fief.localhost"
        )
    settings.hostname = (
        input("Enter the hostname for codecarbon. [codecarbon.localhost]").strip()
        or "codecarbon.localhost"
    )


if __name__ == "__main__":
    app()
