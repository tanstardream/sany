"""业务表：叉车档案 + 故障记录。"""
from datetime import date, datetime

from sqlalchemy import String, Float, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Forklift(Base):
    __tablename__ = "forklifts"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_no: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    model_id: Mapped[int | None] = mapped_column(ForeignKey("models.id"), nullable=True, index=True)
    site_id: Mapped[int | None] = mapped_column(ForeignKey("sites.id"), nullable=True, index=True)
    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="在用")  # 在用 / 停用 / 报废
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class FaultRecord(Base):
    __tablename__ = "fault_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    fault_no: Mapped[str | None] = mapped_column(String(50), index=True)
    forklift_id: Mapped[int | None] = mapped_column(ForeignKey("forklifts.id"), nullable=True, index=True)
    fault_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    system_id: Mapped[int | None] = mapped_column(ForeignKey("systems.id"), nullable=True, index=True)
    symptom_id: Mapped[int | None] = mapped_column(ForeignKey("symptoms.id"), nullable=True, index=True)
    cause_id: Mapped[int | None] = mapped_column(ForeignKey("causes.id"), nullable=True, index=True)
    repair_id: Mapped[int | None] = mapped_column(ForeignKey("repairs.id"), nullable=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    downtime_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    repair_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    handler: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
