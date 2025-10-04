from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    app_env: str = Field(default="dev", alias="APP_ENV")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    cerebras_api_key: str | None = Field(default=None, alias="CEREBRAS_API_KEY")
    postgres_url: str | None = Field(default=None, alias="POSTGRES_URL")
    redis_url: str | None = Field(default=None, alias="REDIS_URL")
    gateway_url: str | None = Field(default=None, alias="GATEWAY_URL")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
