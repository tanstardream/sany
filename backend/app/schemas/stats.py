from pydantic import BaseModel


class Overview(BaseModel):
    total_faults: int
    total_forklifts: int
    this_month_faults: int
    total_downtime_hours: float
    total_repair_cost: float


class NameCount(BaseModel):
    label: str
    value: int


class TrendPoint(BaseModel):
    period: str
    count: int
