"""Data models for Flight Explorer app."""

from pydantic import BaseModel


class Position(BaseModel):
    lat: float
    lng: float
    alt_ft: float  # altitude in feet
    ts: int  # unix timestamp
    heading: float = 0
    speed_kts: float = 0


class Aircraft(BaseModel):
    hex: str  # ICAO 24-bit address
    tail_number: str = ""
    type_code: str = ""  # e.g. "B738"
    manufacturer: str = ""
    model: str = ""
    owner: str = ""
    year_built: int = 0


class OverheadPass(BaseModel):
    hex: str
    tail_number: str = ""
    aircraft_type: str = ""
    callsign: str = ""
    altitude_ft: float
    distance_nm: float  # closest approach distance
    timestamp: int
    heading: float = 0
    speed_kts: float = 0
    origin: str = ""
    destination: str = ""


class FlightTrack(BaseModel):
    hex: str
    callsign: str = ""
    date: str
    positions: list[Position]
    origin: str = ""
    destination: str = ""
