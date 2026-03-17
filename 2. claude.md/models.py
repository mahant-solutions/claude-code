"""Pydantic models for API responses — no raw dicts (CLAUDE.md rule)."""

from pydantic import BaseModel


class WeatherCondition(BaseModel):
    text: str


class CurrentWeather(BaseModel):
    temp_c: float
    humidity: int
    condition: WeatherCondition


class Location(BaseModel):
    name: str
    region: str
    country: str


class WeatherResponse(BaseModel):
    location: Location
    current: CurrentWeather
