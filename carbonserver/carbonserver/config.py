from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    db_url: str = Field("postgresql://codecarbon-user:supersecret@localhost:5480/codecarbon_db", env="DATABASE_URL")


settings = Settings()
