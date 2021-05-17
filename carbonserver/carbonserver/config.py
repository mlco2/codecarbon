from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    db_url: str = Field("sqlite:///./code_carbon.db", env="DATABASE_URL")


settings = Settings()
