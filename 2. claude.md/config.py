"""App config via pydantic-settings — validates env vars at startup (Design Best Practice)."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    weather_api_key: str = ""
    weather_api_base_url: str = "https://api.weatherapi.com/v1"
    weather_api_timeout: float = 10.0

    model_config = {"env_file": ".env"}


settings = Settings()
