# 叉车故障记录系统

关系型字典控制的叉车故障录入 / 查询 / 统计系统。前后端分离：
后端 **FastAPI + SQLite**，前端 **Vue3 + Element Plus + ECharts**，纯静态前端可托管到任意位置（如 GitHub Pages），运行时选择后端地址。

## 功能

- 故障录入：叉车 / 日期 / 系统 / 现象 / 原因 / 维修方式 / 停机时长 / 费用 / 描述
- **关系型字典控制内容**：系统、原因、型号、品牌、地点、现象、维修方式均为受控字典，外键引用，用户可自定义
- **录入优先复用 + 智能防重复**：新建字典项时先做模糊匹配，提示相似已有项（避免"轴瓦螺丝掉落 / 轴瓦损坏"重复），确认后才新建
- 故障查询：多条件筛选（系统/原因/日期/地点/型号）+ 关键词 + 分页
- 统计分析：概览卡片 + 按系统/原因/型号/地点分布图 + 月度趋势（ECharts）
- 叉车档案、字典管理（增删改、停用、引用保护）、用户管理（账号密码）
- CSV / xlsx 批量导入（含中文编码自动探测）+ 模板下载
- 单角色：所有登录用户均可增删改查，按账号区分（记录录入人）

默认管理员：`admin / admin123`（首次登录后请到"用户管理"修改密码）。

## 目录结构

```
forklift-fault/
├── backend/          FastAPI + SQLite 后端
│   ├── app/          代码（models / schemas / routers / services）
│   ├── deploy/       启动脚本 + systemd 单元
│   └── requirements.txt
└── frontend/         Vue3 静态前端（可作为独立 git 仓库）
    ├── src/
    ├── .github/workflows/deploy.yml   GitHub Pages 自动部署
    └── vite.config.js
```

## 本地开发

后端：
```bat
cd backend
py -3.14 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
deploy\start.bat          REM 等价于 uvicorn app.main:app --port 8000 --reload
```

前端（开发模式自动把 /api 代理到 http://127.0.0.1:8000）：
```bat
cd frontend
npm install
npm run dev               REM 打开 http://localhost:5173
```

构建生产静态包：
```bat
cd frontend
npm run build             REM 产物在 frontend/dist/
```

后端冒烟测试：`backend\.venv\Scripts\python.exe smoke_test.py`

## 部署

### 后端 → 服务器（如 10.0.0.152）

1. 上传 `backend/` 到服务器（如 `/opt/forklift-fault/backend`）。
2. 服务器建虚拟环境并安装依赖：`python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt`。
3. 用 systemd 托管（见 `backend/deploy/forklift-fault.service`），或直接 `deploy/start.sh`。
4. 设置环境变量覆盖默认密钥与初始密码：`JWT_SECRET`、`ADMIN_PASSWORD`。

### 前端 → GitHub Pages

1. 把 `frontend/` 作为独立 git 仓库推到 GitHub（`.github/workflows/deploy.yml` 会在 push 到 main 时自动构建并发布到 Pages）。
2. 仓库 Settings → Pages → Source 选 **GitHub Actions**。
3. 访问 `https://<账号>.github.io/<仓库名>/`，首次进入在"后端设置"填后端地址。

> 已用 hash 路由 + 相对 base，任意子路径下刷新都不会 404。

## ⚠️ 关键部署注意事项：HTTPS 与混合内容

**GitHub Pages 强制 HTTPS，而 `http://10.0.0.152:8000` 是 HTTP 且为内网地址。** 浏览器会拦截 HTTPS 页面对 HTTP 接口的请求（混合内容），且公网/外网设备无法访问内网 IP。要让 GitHub Pages 前端能调用后端，二选一：

- **方案 A（推荐，可外网访问）**：用隧道（cloudflared / frp / ngrok）把后端暴露成**公网 HTTPS 地址**，在前端"后端设置"里填这个 https 地址。
- **方案 B（仅内网）**：让后端直接出 HTTPS（自签证书，`uvicorn ... --ssl-keyfile k.pem --ssl-certfile c.pem`），用户首次需手动信任证书；且仅同局域网设备可访问。
- **方案 C（最省事，绕开 GitHub Pages）**：把前端 `dist/` 直接放到后端服务器，由后端/Nginx 同源提供 HTTP 页面 —— 同源 HTTP 不存在混合内容问题，适合纯内网使用。

> 若仅在内网用、且希望走 GitHub Pages，至少需要"方案 B"的 HTTPS，否则浏览器必定拦截。

## 数据模型（关系型控制）

- 字典表（用户可维护）：`brands / models(品牌外键) / sites / systems / symptoms / causes / repairs`
- 业务表：`forklifts`（型号/地点外键）、`fault_records`（叉车 + 系统/现象/原因/维修 外键 + 录入人）
- 删除字典项若已被引用则拒绝，改为"停用"，保证历史统计准确。
