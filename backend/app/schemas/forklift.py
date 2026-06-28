from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ForkliftBase(BaseModel):
    asset_no: str
    model_id: int | None = None
    site_id: int | None = None
    purchase_date: date | None = None
    department: str | None = None
    status: str = "在用"
    remark: str | None = None


class ForkliftCreate(ForkliftBase):
    pass


class ForkliftUpdate(ForkliftBase):
    pass


class ForkliftOut(ForkliftBase):
    id: int
    # 以下为关联展平字段，由路由层填充
    model_name: str | None = None
    brand_name: str | None = None
    site_name: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
