from decimal import Decimal

from pydantic import BaseModel


class MonthlyTrendItem(BaseModel):
    period: str          # YYYY-MM
    total_charges: Decimal
    total_payments: Decimal
    collection_rate: str  # "85.50" gibi string (JSON uyumlu)


class FlatOccupancyStats(BaseModel):
    total_flats: int
    active_flats: int
    occupied_flats: int   # en az bir aktif sakin ilişkisi olan daire
    vacant_flats: int     # aktif ama sakinsiz daire


class ChargeTypeBreakdownItem(BaseModel):
    charge_type: str
    total_amount: Decimal
    charge_count: int


class AnalyticsDashboardResponse(BaseModel):
    monthly_trend: list[MonthlyTrendItem]
    occupancy: FlatOccupancyStats
    charge_type_breakdown: list[ChargeTypeBreakdownItem]
    avg_collection_rate: str   # son 12 ayın ortalaması
