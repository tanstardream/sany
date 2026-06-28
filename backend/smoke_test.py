r"""端到端冒烟测试：用临时 SQLite，验证核心闭环。

运行: .venv\Scripts\python.exe smoke_test.py
"""
import os
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 在导入 app 前指定临时库，避免污染开发库
_tmpdb = Path(tempfile.gettempdir()) / "ff_smoke.db"
if _tmpdb.exists():
    _tmpdb.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmpdb}"
os.environ["ADMIN_PASSWORD"] = "admin123"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

with TestClient(app) as c:
    # 1. 健康检查
    assert c.get("/api/health").json()["status"] == "ok"

    # 2. 登录
    r = c.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    # 未带 token 应 401
    assert c.get("/api/dicts/systems").status_code == 401

    # 3. 建字典：品牌/地点/型号/系统，以及"轴瓦螺丝掉落"故障原因
    brand_id = c.post("/api/dicts/brands", json={"name": "三一"}, headers=h).json()["id"]
    site_id = c.post("/api/dicts/sites", json={"name": "遵义"}, headers=h).json()["id"]
    model_id = c.post("/api/dicts/models", json={"name": "35F7", "brand_id": brand_id}, headers=h).json()["id"]
    sys_id = c.post("/api/dicts/systems", json={"name": "传动系统"}, headers=h).json()["id"]
    cau1 = c.post("/api/dicts/causes", json={"name": "轴瓦螺丝掉落"}, headers=h).json()

    # 4. 防重复：查"轴瓦损坏"应命中"轴瓦螺丝掉落"
    sim = c.get("/api/dicts/causes/similar?q=轴瓦损坏", headers=h).json()
    print("相似项(轴瓦损坏):", sim)
    assert any(s["name"] == "轴瓦螺丝掉落" for s in sim), "应检测到相似原因"

    # 精确同名应 409
    dup = c.post("/api/dicts/causes", json={"name": "轴瓦螺丝掉落"}, headers=h)
    assert dup.status_code == 409, dup.text

    # 5. 叉车建档 + 录故障
    fl = c.post("/api/forklifts", json={
        "asset_no": "FL-001", "model_id": model_id, "site_id": site_id, "department": "物流部",
    }, headers=h).json()
    assert fl["brand_name"] == "三一" and fl["model_name"] == "35F7" and fl["site_name"] == "遵义"

    fault = c.post("/api/faults", json={
        "forklift_id": fl["id"], "fault_date": "2026-06-28", "system_id": sys_id,
        "cause_id": cau1["id"], "description": "轴瓦螺丝掉落，已更换", "downtime_hours": 4, "handler": "张三",
    }, headers=h).json()
    print("故障编号:", fault["fault_no"], "| 原因:", fault["cause_name"], "| 型号:", fault["model_name"])

    # 6. 列表 + 关键词搜索
    lst = c.get("/api/faults?q=轴瓦", headers=h).json()
    assert lst["total"] == 1 and lst["items"][0]["cause_name"] == "轴瓦螺丝掉落"

    # 7. 统计
    ov = c.get("/api/stats/overview", headers=h).json()
    print("概览:", ov)
    assert ov["total_faults"] == 1
    print("按原因:", c.get("/api/stats/by-dim?dim=cause", headers=h).json())
    print("趋势:", c.get("/api/stats/trend", headers=h).json())

    # 8. 引用保护：删除被引用的原因应 409
    delr = c.delete(f"/api/dicts/causes/{cau1['id']}", headers=h)
    assert delr.status_code == 409, delr.text
    print("删除被引用项:", delr.status_code, delr.json()["detail"])

    # 9. 停用(软删除)可用
    dis = c.put(f"/api/dicts/causes/{cau1['id']}", json={"is_active": False}, headers=h).json()
    assert dis["is_active"] is False

    # 10. 用户管理 + 改密
    u2 = c.post("/api/users", json={"username": "tester", "password": "pw123"}, headers=h).json()
    c.put(f"/api/users/{u2['id']}", json={"password": "newpw"}, headers=h)
    # 用新密码登录
    assert c.post("/api/auth/login", json={"username": "tester", "password": "newpw"}).status_code == 200

print("\n✅ 全部后端冒烟测试通过")
