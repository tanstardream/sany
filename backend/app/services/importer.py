"""CSV / xlsx 解析与故障批量导入。

- CSV 自动探测编码(UTF-8 / GBK)，解决 Windows 中文 Excel 导出乱码。
- xlsx 用 openpyxl 读取。
- 导入时字典项(系统/原因/型号/现象/维修)不存在则自动新建（按用户选择）。
- 叉车资产必须已建档；缺失则在错误报告中标注。
"""
from __future__ import annotations

import io
import csv
from datetime import date, datetime

import chardet
import openpyxl
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.asset import FaultRecord, Forklift
from ..models.dictionary import Cause, Repair, Symptom, System

COLUMNS = [
    "叉车资产编号", "故障日期", "故障系统", "故障现象", "故障原因",
    "维修方式", "停机时长", "维修费用", "处理人", "详细描述",
]


def read_rows(content: bytes, filename: str) -> list[dict]:
    name = (filename or "").lower()
    if name.endswith(".xlsx") or name.endswith(".xlsm"):
        return _read_xlsx(content)
    return _read_csv(content)


def _read_xlsx(content: bytes) -> list[dict]:
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    ws = wb.active
    rows_iter = ws.iter_rows(values_only=True)
    try:
        header = [str(c).strip() if c is not None else "" for c in next(rows_iter)]
    except StopIteration:
        return []
    data: list[dict] = []
    for r in rows_iter:
        if all(v is None or str(v).strip() == "" for v in r):
            continue
        data.append({header[i]: r[i] for i in range(min(len(header), len(r)))})
    return data


def _read_csv(content: bytes) -> list[dict]:
    enc = chardet.detect(content).get("encoding") or "utf-8"
    try:
        text = content.decode(enc, errors="replace")
    except (LookupError, TypeError):
        text = content.decode("utf-8-sig", errors="replace")
    # 去掉 BOM
    if text and text[0] == "﻿":
        text = text[1:]
    return [dict(r) for r in csv.DictReader(io.StringIO(text))]


def _parse_date(val) -> date | None:
    if val is None or str(val).strip() == "":
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    s = str(val).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _to_float(val) -> float | None:
    if val is None or str(val).strip() == "":
        return None
    try:
        return float(str(val).strip())
    except ValueError:
        return None


def _get_or_create(db: Session, model, name):
    """返回 (obj_or_None, created_bool)。"""
    name = (name or "").strip()
    if not name:
        return None, False
    obj = db.execute(select(model).where(model.name == name)).scalars().first()
    if obj:
        return obj, False
    obj = model(name=name)
    db.add(obj)
    db.flush()
    return obj, True


def import_faults(db: Session, rows: list[dict], created_by: int) -> dict:
    created = 0
    errors: list[str] = []
    auto_created: dict[str, list[str]] = {
        "systems": [], "symptoms": [], "causes": [], "repairs": [],
    }
    bucket_map = {System: "systems", Symptom: "symptoms", Cause: "causes", Repair: "repairs"}

    for idx, row in enumerate(rows, start=2):  # start=2 计上表头行
        asset = str(row.get("叉车资产编号", "")).strip()
        if not asset:
            errors.append(f"第{idx}行: 叉车资产编号为空")
            continue
        fl = db.execute(select(Forklift).where(Forklift.asset_no == asset)).scalars().first()
        if not fl:
            errors.append(f"第{idx}行: 叉车资产编号「{asset}」不存在，请先在叉车档案建档")
            continue

        fdate = _parse_date(row.get("故障日期"))
        if not fdate:
            errors.append(f"第{idx}行: 故障日期格式错误「{row.get('故障日期')}」(应为 YYYY-MM-DD)")
            continue

        refs = {}
        for model in (System, Symptom, Cause, Repair):
            header = {
                System: "故障系统", Symptom: "故障现象",
                Cause: "故障原因", Repair: "维修方式",
            }[model]
            obj, was_created = _get_or_create(db, model, row.get(header))
            if obj and was_created:
                auto_created[bucket_map[model]].append(obj.name)
            refs[model] = obj

        fr = FaultRecord(
            forklift_id=fl.id,
            fault_date=fdate,
            system_id=refs[System].id if refs[System] else None,
            symptom_id=refs[Symptom].id if refs[Symptom] else None,
            cause_id=refs[Cause].id if refs[Cause] else None,
            repair_id=refs[Repair].id if refs[Repair] else None,
            downtime_hours=_to_float(row.get("停机时长")),
            repair_cost=_to_float(row.get("维修费用")),
            handler=(str(row.get("处理人") or "").strip() or None),
            description=(str(row.get("详细描述") or "").strip() or None),
            created_by=created_by,
        )
        db.add(fr)
        db.flush()
        fr.fault_no = f"F{fr.id:06d}"
        created += 1

    db.commit()
    # 去重自动新建清单
    for k in auto_created:
        auto_created[k] = sorted(set(auto_created[k]))
    return {
        "total_rows": len(rows),
        "created": created,
        "errors": errors,
        "auto_created": auto_created,
    }
