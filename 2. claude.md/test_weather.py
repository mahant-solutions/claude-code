"""Tests for weather module."""

from models import CurrentWeather, Location, WeatherCondition, WeatherResponse
from weather import fetch_weather, format_weather


def test_format_weather() -> None:
    data = WeatherResponse(
        location=Location(name="London", region="City of London", country="UK"),
        current=CurrentWeather(
            temp_c=15.0,
            humidity=72,
            condition=WeatherCondition(text="Partly cloudy"),
        ),
    )
    output = format_weather(data)
    assert "London" in output
    assert "15.0°C" in output
    assert "72%" in output
    assert "Partly cloudy" in output
