from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    db_url: str = Field(
        "postgresql://codecarbon-user:supersecret@localhost:5432/codecarbon_db",
        env="DATABASE_URL",
    )
    # Authentication provider settings
    auth_provider: str = Field(
        "oidc", env="AUTH_PROVIDER"
    )  # Options: 'oidc', 'fief' (deprecated), 'none'

    # OIDC settings (with backward compatibility for Fief environment variables)
    oidc_client_id: str = ""
    oidc_client_secret: str = ""
    oidc_issuer_url: str = "https://auth.codecarbon.io/codecarbon-dev"
    oidc_well_known_url: str = ""
    frontend_url: str = Field("", env="FRONTEND_URL")
    environment: str = Field("production")
    jwt_key: str = Field("", env="JWT_KEY")
    api_port: int = Field(8080, env="API_PORT")
    server_host: str = Field("0.0.0.0", env="SERVER_HOST")

    # Fief settings (deprecated)
    fief_client_id: str = ""
    fief_client_secret: str = ""
    fief_url: str = ""

    class Config:
        # Define alternative environment variable names for backward compatibility
        fields = {
            "oidc_client_id": {"env": ["OIDC_CLIENT_ID"]},
            "oidc_client_secret": {"env": ["OIDC_CLIENT_SECRET"]},
            "oidc_issuer_url": {"env": ["OIDC_ISSUER_URL"]},
            "fief_client_id": {"env": ["FIEF_CLIENT_ID"]},
            "fief_client_secret": {"env": ["FIEF_CLIENT_SECRET"]},
            "fief_url": {"env": ["FIEF_URL"]},
            "oidc_well_known_url": {
                "env": [
                    "OIDC_WELL_KNOWN_URL",
                    "FIEF_URL" + "/.well-known/openid-configuration",
                ]
            },
        }


settings = Settings()
