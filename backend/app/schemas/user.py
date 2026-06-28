from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    id: int
    username: str
    display_name: str | None = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: str
    password: str
    display_name: str | None = None


class UserUpdate(BaseModel):
    password: str | None = None
    display_name: str | None = None
    is_active: bool | None = None
