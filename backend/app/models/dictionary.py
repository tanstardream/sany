"""字典表（受控词汇）。

所有"系统/原因/型号/品牌/地点/现象/维修方式"都做成独立字典表，
故障与叉车通过外键引用，从而"控制内容"。用户可在前端对这些字典增删改。
删除时若已被业务表引用，则改为"停用"而非物理删除，保证历史统计准确。
"""
from datetime import datetime

from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class DictBase:
    """字典表通用字段混入。"""

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Brand(DictBase, Base):
    __tablename__ = "brands"


class ForkliftModel(DictBase, Base):
    __tablename__ = "models"
    brand_id: Mapped[int | None] = mapped_column(ForeignKey("brands.id"), nullable=True, index=True)
    specs: Mapped[str | None] = mapped_column(String(200), nullable=True)


class Site(DictBase, Base):
    __tablename__ = "sites"


class System(DictBase, Base):
    __tablename__ = "systems"


class Symptom(DictBase, Base):
    __tablename__ = "symptoms"


class Cause(DictBase, Base):
    __tablename__ = "causes"


class Repair(DictBase, Base):
    __tablename__ = "repairs"
