"""统计聚合：概览 + 按维度分组 + 时间趋势。

注：日期分组用 SQLite 的 strftime，因此该路由与 SQLite 耦合
(项目已选定 SQLite；若换库需改为对应方言)。
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models.asset import FaultRecord, Forklift
from ..models.dictionary import Brand, Cause, ForkliftModel, Site, System
from ..schemas.stats import NameCount, Overview, TrendPoint

router = APIRouter(prefix="/api/stats", tags=["统计分析"], dependencies=[Depends(get_current_user)])

DIM_TABLE = {
    "system": System,
    "cause": Cause,
    "model": ForkliftModel,
    "site": Site,
    "brand": Brand,
}


@router.get("/overview", response_model=Overview)
def overview(db: Session = Depends(get_db)):
    total_faults = db.execute(select(func.count(FaultRecord.id))).scalar() or 0
    total_forklifts = db.execute(select(func.count(Forklift.id))).scalar() or 0
    now = date.today()
    this_month = db.execute(
        select(func.count(FaultRecord.id)).where(
            func.strftime("%Y", FaultRecord.fault_date) == str(now.year),
            func.strftime("%m", FaultRecord.fault_date) == f"{now.month:02d}",
        )
    ).scalar() or 0
    downtime = db.execute(
        select(func.coalesce(func.sum(FaultRecord.downtime_hours), 0.0))
    ).scalar() or 0.0
    cost = db.execute(
        select(func.coalesce(func.sum(FaultRecord.repair_cost), 0.0))
    ).scalar() or 0.0
    return Overview(
        total_faults=total_faults,
        total_forklifts=total_forklifts,
        this_month_faults=this_month,
        total_downtime_hours=float(downtime),
        total_repair_cost=float(cost),
    )


@router.get("/by-dim", response_model=list[NameCount])
def by_dim(
    dim: str = "system",
    start_date: date | None = None,
    end_date: date | None = None,
    top: int = 0,
    db: Session = Depends(get_db),
):
    if dim not in DIM_TABLE:
        raise HTTPException(status_code=400, detail="不支持该维度")
    Table = DIM_TABLE[dim]
    stmt = select(Table.name.label("label"), func.count().label("value")).select_from(FaultRecord)
    if dim == "system":
        stmt = stmt.join(System, FaultRecord.system_id == System.id)
    elif dim == "cause":
        stmt = stmt.join(Cause, FaultRecord.cause_id == Cause.id)
    elif dim == "model":
        stmt = (
            stmt.join(Forklift, FaultRecord.forklift_id == Forklift.id)
            .join(ForkliftModel, Forklift.model_id == ForkliftModel.id)
        )
    elif dim == "site":
        stmt = (
            stmt.join(Forklift, FaultRecord.forklift_id == Forklift.id)
            .join(Site, Forklift.site_id == Site.id)
        )
    elif dim == "brand":
        stmt = (
            stmt.join(Forklift, FaultRecord.forklift_id == Forklift.id)
            .join(ForkliftModel, Forklift.model_id == ForkliftModel.id)
            .join(Brand, ForkliftModel.brand_id == Brand.id)
        )
    if start_date:
        stmt = stmt.where(FaultRecord.fault_date >= start_date)
    if end_date:
        stmt = stmt.where(FaultRecord.fault_date <= end_date)
    stmt = stmt.group_by(Table.name).order_by(func.count().desc())
    if top:
        stmt = stmt.limit(top)
    rows = db.execute(stmt).all()
    return [NameCount(label=r.label, value=r.value) for r in rows]


@router.get("/trend", response_model=list[TrendPoint])
def trend(
    granularity: str = "month",
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    fmt = "%Y" if granularity == "year" else "%Y-%m"
    period_expr = func.strftime(fmt, FaultRecord.fault_date).label("period")
    stmt = select(period_expr, func.count().label("count"))
    if start_date:
        stmt = stmt.where(FaultRecord.fault_date >= start_date)
    if end_date:
        stmt = stmt.where(FaultRecord.fault_date <= end_date)
    stmt = stmt.group_by(period_expr).order_by(period_expr)
    rows = db.execute(stmt).all()
    return [TrendPoint(period=r.period, count=r.count) for r in rows]
