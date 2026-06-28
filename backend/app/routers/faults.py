"""故障记录：分页列表(多条件筛选+关键词)、详情、增删改。"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models.asset import FaultRecord, Forklift
from ..models.dictionary import Brand, Cause, ForkliftModel, Repair, Site, Symptom, System
from ..models.user import User
from ..schemas.common import Page
from ..schemas.fault import FaultCreate, FaultOut, FaultUpdate

router = APIRouter(prefix="/api/faults", tags=["故障记录"], dependencies=[Depends(get_current_user)])


def _base_query():
    """故障主表 + 关联展平列(品牌/型号/地点/系统/现象/原因/维修/录入人)。"""
    return (
        select(
            FaultRecord,
            Forklift.asset_no.label("forklift_asset_no"),
            ForkliftModel.name.label("model_name"),
            Brand.name.label("brand_name"),
            Site.name.label("site_name"),
            System.name.label("system_name"),
            Symptom.name.label("symptom_name"),
            Cause.name.label("cause_name"),
            Repair.name.label("repair_name"),
            User.username.label("created_by_name"),
        )
        .select_from(FaultRecord)
        .join(Forklift, FaultRecord.forklift_id == Forklift.id, isouter=True)
        .join(ForkliftModel, Forklift.model_id == ForkliftModel.id, isouter=True)
        .join(Brand, ForkliftModel.brand_id == Brand.id, isouter=True)
        .join(Site, Forklift.site_id == Site.id, isouter=True)
        .join(System, FaultRecord.system_id == System.id, isouter=True)
        .join(Symptom, FaultRecord.symptom_id == Symptom.id, isouter=True)
        .join(Cause, FaultRecord.cause_id == Cause.id, isouter=True)
        .join(Repair, FaultRecord.repair_id == Repair.id, isouter=True)
        .join(User, FaultRecord.created_by == User.id, isouter=True)
    )


def _row_to_out(row) -> dict:
    fr = row[0]
    d = FaultOut.model_validate(fr).model_dump()
    d.update(
        forklift_asset_no=row.forklift_asset_no,
        model_name=row.model_name,
        brand_name=row.brand_name,
        site_name=row.site_name,
        system_name=row.system_name,
        symptom_name=row.symptom_name,
        cause_name=row.cause_name,
        repair_name=row.repair_name,
        created_by_name=row.created_by_name,
    )
    return d


def _apply_filters(stmt, params: dict):
    q = params.get("q")
    if q:
        stmt = stmt.where(
            FaultRecord.description.contains(q)
            | FaultRecord.handler.contains(q)
            | FaultRecord.fault_no.contains(q)
            | Forklift.asset_no.contains(q)
        )
    for key, col in (
        ("forklift_id", FaultRecord.forklift_id),
        ("system_id", FaultRecord.system_id),
        ("cause_id", FaultRecord.cause_id),
        ("symptom_id", FaultRecord.symptom_id),
        ("repair_id", FaultRecord.repair_id),
    ):
        v = params.get(key)
        if v:
            stmt = stmt.where(col == v)
    if params.get("site_id"):
        stmt = stmt.where(Forklift.site_id == params["site_id"])
    if params.get("model_id"):
        stmt = stmt.where(Forklift.model_id == params["model_id"])
    if params.get("start_date"):
        stmt = stmt.where(FaultRecord.fault_date >= params["start_date"])
    if params.get("end_date"):
        stmt = stmt.where(FaultRecord.fault_date <= params["end_date"])
    return stmt


@router.get("", response_model=Page[FaultOut])
def list_faults(
    q: str | None = None,
    forklift_id: int | None = None,
    system_id: int | None = None,
    cause_id: int | None = None,
    symptom_id: int | None = None,
    repair_id: int | None = None,
    site_id: int | None = None,
    model_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    params = dict(q=q, forklift_id=forklift_id, system_id=system_id, cause_id=cause_id,
                  symptom_id=symptom_id, repair_id=repair_id, site_id=site_id,
                  model_id=model_id, start_date=start_date, end_date=end_date)
    base = _apply_filters(_base_query(), params)
    total = db.execute(select(func.count()).select_from(base.subquery())).scalar() or 0
    rows = (
        db.execute(
            base.order_by(FaultRecord.fault_date.desc(), FaultRecord.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        .all()
    )
    return Page[FaultOut](
        items=[_row_to_out(r) for r in rows], total=total, page=page, size=size
    )


@router.get("/{fid}", response_model=FaultOut)
def get_fault(fid: int, db: Session = Depends(get_db)):
    row = db.execute(_base_query().where(FaultRecord.id == fid)).first()
    if not row:
        raise HTTPException(status_code=404, detail="故障不存在")
    return _row_to_out(row)


@router.post("", response_model=FaultOut, status_code=201)
def create_fault(
    data: FaultCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    if data.forklift_id and not db.get(Forklift, data.forklift_id):
        raise HTTPException(status_code=400, detail="所选叉车不存在")
    fr = FaultRecord(**data.model_dump(), created_by=current.id)
    db.add(fr)
    db.flush()
    fr.fault_no = f"F{fr.id:06d}"
    db.commit()
    db.refresh(fr)
    row = db.execute(_base_query().where(FaultRecord.id == fr.id)).first()
    return _row_to_out(row)


@router.put("/{fid}", response_model=FaultOut)
def update_fault(fid: int, data: FaultUpdate, db: Session = Depends(get_db)):
    fr = db.get(FaultRecord, fid)
    if not fr:
        raise HTTPException(status_code=404, detail="故障不存在")
    for k, v in data.model_dump().items():
        setattr(fr, k, v)
    db.commit()
    db.refresh(fr)
    row = db.execute(_base_query().where(FaultRecord.id == fr.id)).first()
    return _row_to_out(row)


@router.delete("/{fid}")
def delete_fault(fid: int, db: Session = Depends(get_db)):
    fr = db.get(FaultRecord, fid)
    if not fr:
        raise HTTPException(status_code=404, detail="故障不存在")
    db.delete(fr)
    db.commit()
    return {"ok": True}
