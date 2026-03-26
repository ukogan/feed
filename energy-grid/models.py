"""Data models for Energy Grid app."""

from pydantic import BaseModel


class FuelGeneration(BaseModel):
    respondent: str  # ISO code e.g. "CISO", "PJM", "ERCO"
    respondent_name: str
    fuel_type: str  # e.g. "SUN", "WND", "NG", "COL", "NUC"
    value_mwh: float
    period: str  # ISO datetime string


class ISOSummary(BaseModel):
    respondent: str
    respondent_name: str
    total_mwh: float
    renewable_pct: float
    carbon_intensity: float  # gCO2/kWh
    fuel_breakdown: dict[str, float]  # fuel_type -> MWh


class ChargingAdvice(BaseModel):
    hour: int
    carbon_intensity: float
    renewable_pct: float
    recommendation: str  # "best", "good", "avoid"
    reason: str
