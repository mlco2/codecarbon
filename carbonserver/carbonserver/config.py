from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    db_url: str = Field(
        "postgresql://codecarbon-user:supersecret@localhost:5432/codecarbon_db",
        env="DATABASE_URL",
    )
    fief_client_id: str = Field("", env="FIEF_CLIENT_ID")
    fief_client_secret: str = Field("", env="FIEF_CLIENT_SECRET")
    fief_url: str = Field("https://auth.codecarbon.io/codecarbon-dev", env="FIEF_URL")
    frontend_url: str = Field("", env="FRONTEND_URL")
    environment: str = Field("production")
    jwt_key: str = Field("", env="JWT_KEY")


settings = Settings()
# print("Database", settings.db_url)
