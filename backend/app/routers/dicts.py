"""字典通用 CRUD + 相似项提示。

所有受控词汇(品牌/型号/地点/系统/现象/原因/维修)共用一套接口，
通过 {dtype} 区分。删除时若已被业务表引用则拒绝(改用停用)。
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func as sqlfunc, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models.asset import FaultRecord, Forklift
from ..models.dictionary import Brand, Cause, ForkliftModel, Repair, Site, Symptom, System
from ..schemas.dict import DictItemCreate, DictItemOut, DictItemUpdate, SimilarItem
from ..services.dedup import find_similar

router = APIRouter(prefix="/api/dicts", tags=["字典管理"], dependencies=[Depends(get_current_user)])

DICT_MODELS = {
    "brands": Brand,
    "models": ForkliftModel,
    "sites": Site,
    "systems": System,
    "symptoms": Symptom,
    "causes": Cause,
    "repairs": Repair,
}

# 反向引用关系：删除字典项前据此判断是否被使用
REFERENCE = {
    "brands": (ForkliftModel, "brand_id"),
    "models": (Forklift, "model_id"),
    "sites": (Forklift, "site_id"),
    "systems": (FaultRecord, "system_id"),
    "symptoms": (FaultRecord, "symptom_id"),
    "causes": (FaultRecord, "cause_id"),
    "repairs": (FaultRecord, "repair_id"),
}

DICT_LABELS = {
    "brands": "品牌", "models": "型号", "sites": "地点",
    "systems": "故障系统", "symptoms": "故障现象",
    "causes": "故障原因", "repairs": "维修方式",
}


def _get_model(dtype: str):
    if dtype not in DICT_MODELS:
        raise HTTPException(status_code=404, detail=f"未知的字典类型: {dtype}")
    return DICT_MODELS[dtype]


def _serialize(db: Session, dtype: str, obj) -> dict:
    d = DictItemOut.model_validate(obj).model_dump()
    if dtype == "models" and obj.brand_id:
        b = db.get(Brand, obj.brand_id)
        d["brand_name"] = b.name if b else None
    return d


@router.get("/{dtype}")
def list_items(
    dtype: str,
    q: str | None = None,
    active: bool | None = None,
    db: Session = Depends(get_db),
):
    Model = _get_model(dtype)
    stmt = select(Model)
    if active is not None:
        stmt = stmt.where(Model.is_active == active)
    if q:
        stmt = stmt.where(Model.name.contains(q))
    stmt = stmt.order_by(Model.sort_order, Model.id)
    rows = db.execute(stmt).scalars().all()
    return [_serialize(db, dtype, r) for r in rows]


@router.get("/{dtype}/similar", response_model=list[SimilarItem])
def similar_items(
    dtype: str,
    q: str = Query(..., min_length=1, description="待查重的名称"),
    db: Session = Depends(get_db),
):
    """新建字典项前的防重复提示：返回相似的已有项。"""
    Model = _get_model(dtype)
    rows = db.execute(select(Model.id, Model.name)).all()
    items = [(r[0], r[1]) for r in rows]
    matched = find_similar(q, items, threshold=60, limit=5)
    return [SimilarItem(id=i, name=n, score=s) for (i, n), s in matched]


@router.post("/{dtype}", status_code=201)
def create_item(dtype: str, data: DictItemCreate, db: Session = Depends(get_db)):
    Model = _get_model(dtype)
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="名称不能为空")
    exists = db.execute(
        select(Model).where(sqlfunc.lower(Model.name) == name.lower())
    ).scalars().first()
    if exists:
        raise HTTPException(status_code=409, detail=f"已存在同名项「{exists.name}」")
    obj = Model(name=name, code=data.code, sort_order=data.sort_order, is_active=data.is_active)
    if dtype == "models":
        obj.brand_id = data.brand_id
        obj.specs = data.specs
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return _serialize(db, dtype, obj)


@router.put("/{dtype}/{item_id}")
def update_item(dtype: str, item_id: int, data: DictItemUpdate, db: Session = Depends(get_db)):
    Model = _get_model(dtype)
    obj = db.get(Model, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail="字典项不存在")
    if data.name is not None:
        nm = data.name.strip()
        dup = db.execute(
            select(Model).where(
                sqlfunc.lower(Model.name) == nm.lower(),
                Model.id != item_id,
            )
        ).scalars().first()
        if dup:
            raise HTTPException(status_code=409, detail=f"已存在同名项「{dup.name}」")
        obj.name = nm
    if data.code is not None:
        obj.code = data.code
    if data.sort_order is not None:
        obj.sort_order = data.sort_order
    if data.is_active is not None:
        obj.is_active = data.is_active
    if dtype == "models":
        if data.brand_id is not None:
            obj.brand_id = data.brand_id
        if data.specs is not None:
            obj.specs = data.specs
    db.commit()
    db.refresh(obj)
    return _serialize(db, dtype, obj)


@router.delete("/{dtype}/{item_id}")
def delete_item(dtype: str, item_id: int, db: Session = Depends(get_db)):
    Model = _get_model(dtype)
    obj = db.get(Model, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail="字典项不存在")
    if dtype in REFERENCE:
        RefModel, col = REFERENCE[dtype]
        cnt = db.execute(
            select(sqlfunc.count()).select_from(RefModel).where(getattr(RefModel, col) == item_id)
        ).scalar()
        if cnt:
            label = DICT_LABELS.get(dtype, "该项")
            raise HTTPException(
                status_code=409,
                detail=f"{label}「{obj.name}」已被 {cnt} 条记录引用，无法删除，请改用停用",
            )
    db.delete(obj)
    db.commit()
    return {"ok": True}
