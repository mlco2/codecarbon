from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    db_url: str = Field(
        "postgresql://codecarbon-user:supersecret@localhost:5432/codecarbon_db",
        env="DATABASE_URL",
    )
    # Authentication provider settings
    auth_provider: str = Field("fief", env="AUTH_PROVIDER")  # Options: 'fief', 'none'

    # Fief-specific settings (kept for backward compatibility)
    fief_client_id: str = Field("", env="FIEF_CLIENT_ID")
    fief_client_secret: str = Field("", env="FIEF_CLIENT_SECRET")
    fief_url: str = Field("https://auth.codecarbon.io/codecarbon-dev", env="FIEF_URL")

    frontend_url: str = Field("", env="FRONTEND_URL")
    environment: str = Field("production")
    jwt_key: str = Field("", env="JWT_KEY")
    logfire_token: str = Field("", env="LOGFIRE_TOKEN")
    send_to_logfire: bool = Field(False, env="LOGFIRE_SEND_TO_LOGFIRE")
    api_port: int = Field(8080, env="API_PORT")
    server_host: str = Field("0.0.0.0", env="SERVER_HOST")


settings = Settings()
