from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    db_url: str = Field(
        "postgresql://codecarbon-user:supersecret@postgres:5432/codecarbon_db",
        env="DATABASE_URL",
    )


settings = Settings()
