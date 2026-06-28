from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class FaultBase(BaseModel):
    forklift_id: int | None = None
    fault_date: date
    system_id: int | None = None
    symptom_id: int | None = None
    cause_id: int | None = None
    repair_id: int | None = None
    description: str | None = None
    downtime_hours: float | None = None
    repair_cost: float | None = None
    handler: str | None = None


class FaultCreate(FaultBase):
    pass


class FaultUpdate(FaultBase):
    pass


class FaultOut(BaseModel):
    id: int
    fault_no: str | None = None
    forklift_id: int | None = None
    forklift_asset_no: str | None = None
    model_name: str | None = None
    brand_name: str | None = None
    site_name: str | None = None
    fault_date: date
    system_id: int | None = None
    system_name: str | None = None
    symptom_id: int | None = None
    symptom_name: str | None = None
    cause_id: int | None = None
    cause_name: str | None = None
    repair_id: int | None = None
    repair_name: str | None = None
    description: str | None = None
    downtime_hours: float | None = None
    repair_cost: float | None = None
    handler: str | None = None
    created_by: int | None = None
    created_by_name: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
