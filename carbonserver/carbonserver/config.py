from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    db_url: str = Field(
        "postgresql://codecarbon-user:supersecret@localhost:5432/codecarbon_db",
        env="DATABASE_URL",
    )
    fief_client_id: str = Field("", env="FIEF_CLIENT_ID")
    fief_client_secret: str = Field("", env="FIEF_CLIENT_SECRET")
    fief_url: str = Field("https://fief.local/mytenant", env="FIEF_URL")


settings = Settings()
# print("Database", settings.db_url)
