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
    occupied_flats: int
    vacant_flats: int


class ChargeTypeBreakdownItem(BaseModel):
    charge_type: str
    total_amount: Decimal
    charge_count: int


class AnalyticsDashboardResponse(BaseModel):
    monthly_trend: list[MonthlyTrendItem]
    occupancy: FlatOccupancyStats
    charge_type_breakdown: list[ChargeTypeBreakdownItem]
    avg_collection_rate: str


class OverdueChargeItem(BaseModel):
    charge_id: str
    flat_id: str
    unit_no: str
    block_name: str
    charge_type: str
    period: str
    amount: Decimal
    due_date: str
    days_overdue: int


class TopDebtorItem(BaseModel):
    flat_id: str
    unit_no: str
    block_name: str
    total_debt: Decimal
    pending_charge_count: int

