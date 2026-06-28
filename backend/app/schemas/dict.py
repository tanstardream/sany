from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DictItemBase(BaseModel):
    name: str
    code: str | None = None
    sort_order: int = 0
    is_active: bool = True


class DictItemCreate(DictItemBase):
    # 仅"型号"使用
    brand_id: int | None = None
    specs: str | None = None


class DictItemUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None
    brand_id: int | None = None
    specs: str | None = None


class DictItemOut(DictItemBase):
    id: int
    brand_id: int | None = None
    specs: str | None = None
    brand_name: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SimilarItem(BaseModel):
    """相似项提示结果。"""

    id: int
    name: str
    score: int  # 0-100 相似度
