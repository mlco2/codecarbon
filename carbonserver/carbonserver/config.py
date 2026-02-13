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

    # Deprecated: Old Fief-specific settings (use OIDC settings instead)
    @property
    def fief_client_id(self) -> str:
        return self.oidc_client_id

    @property
    def fief_client_secret(self) -> str:
        return self.oidc_client_secret

    @property
    def fief_url(self) -> str:
        return self.oidc_issuer_url

    frontend_url: str = Field("", env="FRONTEND_URL")
    environment: str = Field("production")
    jwt_key: str = Field("", env="JWT_KEY")
    api_port: int = Field(8080, env="API_PORT")
    server_host: str = Field("0.0.0.0", env="SERVER_HOST")

    class Config:
        # Define alternative environment variable names for backward compatibility
        fields = {
            "oidc_client_id": {"env": ["OIDC_CLIENT_ID", "FIEF_CLIENT_ID"]},
            "oidc_client_secret": {"env": ["OIDC_CLIENT_SECRET", "FIEF_CLIENT_SECRET"]},
            "oidc_issuer_url": {"env": ["OIDC_ISSUER_URL", "FIEF_URL"]},
        }


settings = Settings()
