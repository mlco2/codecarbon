from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    db_url: str = Field(
        "postgresql://codecarbon-user:supersecret@localhost:5432/codecarbon_db",
        validation_alias=AliasChoices("DATABASE_URL", "db_url"),
    )
    # Authentication provider settings
    auth_provider: str = Field(
        "oidc",
        validation_alias=AliasChoices("AUTH_PROVIDER", "auth_provider"),
    )  # Options: 'oidc', 'fief' (deprecated), 'none'

    # OIDC settings
    oidc_client_id: str = Field(
        "",
        validation_alias=AliasChoices("OIDC_CLIENT_ID", "oidc_client_id"),
    )
    oidc_client_secret: str = Field(
        "",
        validation_alias=AliasChoices("OIDC_CLIENT_SECRET", "oidc_client_secret"),
    )
    oidc_issuer_url: str = Field(
        "https://auth.codecarbon.io/codecarbon-dev",
        validation_alias=AliasChoices("OIDC_ISSUER_URL", "oidc_issuer_url"),
    )
    oidc_well_known_url: str = Field(
        "",
        validation_alias=AliasChoices("OIDC_WELL_KNOWN_URL", "oidc_well_known_url"),
    )
    frontend_url: str = Field(
        "",
        validation_alias=AliasChoices("FRONTEND_URL", "frontend_url"),
    )
    environment: str = Field("production")
    jwt_key: str = Field("", validation_alias=AliasChoices("JWT_KEY", "jwt_key"))
    api_port: int = Field(8080, validation_alias=AliasChoices("API_PORT", "api_port"))
    server_host: str = Field(
        "0.0.0.0", validation_alias=AliasChoices("SERVER_HOST", "server_host")
    )

    # Fief settings (deprecated)
    fief_client_id: str = Field(
        "",
        validation_alias=AliasChoices("FIEF_CLIENT_ID", "fief_client_id"),
    )
    fief_client_secret: str = Field(
        "",
        validation_alias=AliasChoices("FIEF_CLIENT_SECRET", "fief_client_secret"),
    )
    fief_url: str = Field(
        "",
        validation_alias=AliasChoices("FIEF_URL", "fief_url"),
    )


settings = Settings()
