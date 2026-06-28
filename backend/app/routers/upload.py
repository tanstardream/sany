"""批量导入(CSV/xlsx) + 模板下载。"""
import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models.user import User
from ..services.importer import COLUMNS, import_faults, read_rows

router = APIRouter(prefix="/api", tags=["导入"], dependencies=[Depends(get_current_user)])


@router.post("/upload/faults")
async def upload_faults(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="上传文件为空")
    try:
        rows = read_rows(content, file.filename or "")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"文件解析失败: {e}")
    if not rows:
        raise HTTPException(status_code=400, detail="文件无数据行（或缺少表头）")
    return import_faults(db, rows, created_by=current.id)


@router.get("/template/faults")
def download_template(format: str = "csv"):
    if format == "xlsx":
        import openpyxl

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(COLUMNS)
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": 'attachment; filename="fault_template.xlsx"'},
        )
    import csv

    buf = io.StringIO()
    csv.writer(buf).writerow(COLUMNS)
    # utf-8-sig 带 BOM，确保 Excel 正确识别中文
    payload = buf.getvalue().encode("utf-8-sig")
    return StreamingResponse(
        io.BytesIO(payload),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="fault_template.csv"'},
    )
