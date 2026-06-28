from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models.asset import FaultRecord, Forklift
from ..models.dictionary import Brand, ForkliftModel, Site
from ..schemas.common import Page
from ..schemas.forklift import ForkliftCreate, ForkliftOut, ForkliftUpdate

router = APIRouter(prefix="/api/forklifts", tags=["叉车档案"], dependencies=[Depends(get_current_user)])


def _enrich(db: Session, f: Forklift) -> dict:
    d = ForkliftOut.model_validate(f).model_dump()
    if f.model_id:
        m = db.get(ForkliftModel, f.model_id)
        d["model_name"] = m.name if m else None
        if m and m.brand_id:
            b = db.get(Brand, m.brand_id)
            d["brand_name"] = b.name if b else None
    if f.site_id:
        s = db.get(Site, f.site_id)
        d["site_name"] = s.name if s else None
    return d


@router.get("", response_model=Page[ForkliftOut])
def list_forklifts(
    q: str | None = None,
    site_id: int | None = None,
    model_id: int | None = None,
    status: str | None = None,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    base = select(Forklift)
    if q:
        base = base.where(
            Forklift.asset_no.contains(q) | Forklift.department.contains(q)
        )
    if site_id:
        base = base.where(Forklift.site_id == site_id)
    if model_id:
        base = base.where(Forklift.model_id == model_id)
    if status:
        base = base.where(Forklift.status == status)

    total = db.execute(select(func.count()).select_from(base.subquery())).scalar() or 0
    rows = (
        db.execute(
            base.order_by(Forklift.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        .scalars()
        .all()
    )
    return Page[ForkliftOut](
        items=[_enrich(db, f) for f in rows], total=total, page=page, size=size
    )


@router.get("/all", response_model=list[ForkliftOut])
def list_all(db: Session = Depends(get_db)):
    """不分页全集，供下拉选择。"""
    rows = db.execute(select(Forklift).order_by(Forklift.asset_no)).scalars().all()
    return [_enrich(db, f) for f in rows]


@router.post("", response_model=ForkliftOut, status_code=201)
def create_forklift(data: ForkliftCreate, db: Session = Depends(get_db)):
    if db.execute(select(Forklift).where(Forklift.asset_no == data.asset_no)).scalars().first():
        raise HTTPException(status_code=409, detail="资产编号已存在")
    f = Forklift(**data.model_dump())
    db.add(f)
    db.commit()
    db.refresh(f)
    return _enrich(db, f)


@router.put("/{fid}", response_model=ForkliftOut)
def update_forklift(fid: int, data: ForkliftUpdate, db: Session = Depends(get_db)):
    f = db.get(Forklift, fid)
    if not f:
        raise HTTPException(status_code=404, detail="叉车不存在")
    for k, v in data.model_dump().items():
        setattr(f, k, v)
    db.commit()
    db.refresh(f)
    return _enrich(db, f)


@router.delete("/{fid}")
def delete_forklift(fid: int, db: Session = Depends(get_db)):
    f = db.get(Forklift, fid)
    if not f:
        raise HTTPException(status_code=404, detail="叉车不存在")
    ref_cnt = db.execute(
        select(func.count()).select_from(FaultRecord).where(FaultRecord.forklift_id == fid)
    ).scalar()
    if ref_cnt:
        raise HTTPException(status_code=409, detail=f"该叉车有 {ref_cnt} 条故障记录，无法删除")
    db.delete(f)
    db.commit()
    return {"ok": True}
