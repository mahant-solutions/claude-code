"""Weather API client — follows all CLAUDE.md rules and design best practices."""

import logging

import httpx

from config import settings
from models import WeatherResponse

logger = logging.getLogger(__name__)

# Constants for magic values (Design Best Practice)
CURRENT_WEATHER_ENDPOINT = "/current.json"


def fetch_weather(city: str) -> WeatherResponse | None:
    """Fetch current weather from the API (I/O layer — separated from formatting)."""
    if not settings.weather_api_key:
        logger.error("WEATHER_API_KEY not set in .env")
        return None

    # httpx.Client with timeout, not bare httpx.get() (Design Best Practice)
    try:
        with httpx.Client(
            base_url=settings.weather_api_base_url,
            timeout=settings.weather_api_timeout,
        ) as client:
            response = client.get(
                CURRENT_WEATHER_ENDPOINT,
                params={"key": settings.weather_api_key, "q": city},
            )
            response.raise_for_status()
    except httpx.HTTPError as e:
        logger.error("API request failed: %s", e)
        return None

    return WeatherResponse.model_validate(response.json())


def format_weather(data: WeatherResponse) -> str:
    """Format weather data for display (pure logic — no I/O)."""
    return (
        f"\n  {data.location.name}, {data.location.country}\n"
        f"  {data.current.condition.text}\n"
        f"  Temperature: {data.current.temp_c}°C\n"
        f"  Humidity: {data.current.humidity}%\n"
    )
