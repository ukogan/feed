"""Data models for AQI Map app."""

from pydantic import BaseModel


class Station(BaseModel):
    site_id: str
    name: str
    lat: float
    lng: float
    state: str
    county: str


class AQIReading(BaseModel):
    site_id: str
    lat: float
    lng: float
    date: str
    aqi: float
    parameter: str  # "PM2.5" or "Ozone"


class TimeSlice(BaseModel):
    year: int
    month: int
    parameter: str
    readings: list[AQIReading]
