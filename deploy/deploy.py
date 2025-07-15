#!/usr/bin/env python3
import dataclasses
import re
import secrets
import subprocess
import time

import requests
import typer
from cryptography.fernet import Fernet
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Annotated


# TODO: use pydantic settings
class FiefSettings(BaseSettings):
    fief_main_admin_api_key: str
    fief_domain: str

    model_config = SettingsConfigDict(
        env_file="deploy/.env.fief", env_file_encoding="utf-8", extra="allow"
    )


class CarbonServerSettings(BaseSettings):
    app_hostname: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="allow"
    )


app = typer.Typer()


@dataclasses.dataclass
class Settings:
    run_traefik: bool = True
    run_fief: bool = True
    fief_hostname: str = "fief.local"
    hostname: str = "codecarbon.local"
    admin_email: str = "admin@localhost"
    fief_admin_password: str = Fernet.generate_key().decode()  # Generate encryption key
    encrypted_fief_admin_password: str = (
        Fernet(fief_admin_password.encode())
        .encrypt(secrets.token_urlsafe(20).encode())
        .decode()
    )
    use_https: bool = False


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
        "FIEF_MAIN_USER_PASSWORD": settings.encrypted_fief_admin_password,
        "ADMIN_EMAIL": settings.admin_email,
        "FRONTEND_URL": f"http://{settings.hostname}",
        "FIEF_URL": f"http://{settings.fief_hostname}",
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
        "./deploy/.env.webapp.example",
        "webapp/.env.development",
        {
            **variables,
            "NEXT_PUBLIC_BASE_URL": f"http://{settings.hostname}",
            "NEXT_PUBLIC_API_URL": f"http://{settings.hostname}/api",
            "FIEF_BASE_URL": variables["FIEF_URL"],
        },
    )

    print(
        f"""
You might need to add the following entries to your /etc/hosts:
local_ip  {settings.hostname} {settings.fief_hostname} webapp.local

Replace "local_ip" by you local ip, not 127.0.0.1
You might be able to get it with `ip a | grep 192.168 | grep -v br-`


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
    print("You can find somme additional information in deploy/README.md")


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
    carbonserver_settings = CarbonServerSettings()

    api = requests.Session()
    api.headers["Authorization"] = f"Bearer {fief_settings.fief_main_admin_api_key}"
    # TODO: https
    url = f"http://{fief_settings.fief_domain}/admin/api"
    print(f"configuring fief at {url}")

    # fief server might not be running yet
    for _ in range(5):
        if api.get(url + "/clients", verify=False).status_code == 200:
            break
        print("waiting for fief server to come online...")
        time.sleep(5)

    client = api.get(url + "/clients", verify=False).json()["results"][0]
    redir_uris = [
        f"https://{carbonserver_settings.app_hostname}/auth/login",
        f"http://{carbonserver_settings.app_hostname}/auth/login",
        f"https://{fief_settings.fief_domain}/docs/oauth2-redirect",
        f"https://{fief_settings.fief_domain}/admin/auth/callback",
        f"http://{fief_settings.fief_domain}/docs/oauth2-redirect",
        f"http://{fief_settings.fief_domain}/admin/auth/callback",
        f"http://{fief_settings.fief_domain}/callback",
        "http://localhost/callback",
        "http://localhost:51562/callback",
    ]
    api.patch(
        f"{url}/clients/{client['id']}",
        json={"redirect_uris": redir_uris},
        verify=False,
    )
    client = api.get(url + "/clients", verify=False).json()["results"][0]

    # cli client
    cli_client = api.post(
        url + "/clients",
        json={
            "name": "cli",
            "first_party": True,
            "client_type": "public",
            "redirect_uris": redir_uris,
            # "authorization_code_lifetime_seconds": 0,
            # "access_id_token_lifetime_seconds": 0,
            # "refresh_token_lifetime_seconds": 0,
            "tenant_id": client["tenant_id"],
        },
    ).json()
    cli_client_id = cli_client["id"]
    print(
        f"""Run the following setup to use the cli:
    export AUTH_SERVER_URL=http://{fief_settings.fief_domain}
    export API_URL=http://{carbonserver_settings.app_hostname}/api
    export AUTH_CLIENT_ID={cli_client_id}
    """
    )


@app.command()
def start(
    traefik: Annotated[bool, typer.Option()] = False,
    fief: Annotated[bool, typer.Option()] = False,
    codecarbon: Annotated[bool, typer.Option()] = False,
):
    try:
        subprocess.check_output(["docker", "network", "create", "shared"])
    except Exception:
        ...

    print("Building images")
    subprocess.check_output(
        [
            "docker-compose",
            "build",
        ],
        cwd="./",
    )

    if traefik:
        print("Starting traefik")
        subprocess.check_output(
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
        """
=========================================
Your codecarbon server is now running !
You can access it:
http://codecarbon.local
"""
    )
    if fief:
        print(
            """
The fief server is running:
http://fief.localhost
"""
        )
    print(
        """
You can run the webapp locally for local development on the port 3000 and access it:
http://webapp.local

The registration code for new users can be found by running:
docker logs fief_fief-worker_1
          """
    )


@app.command()
def setup():
    print("This will setup local docker compose files.")
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
    _setup(settings)


if __name__ == "__main__":
    app()
