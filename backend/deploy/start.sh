#!/usr/bin/env bash
# 服务器上启动后端(单进程 uvicorn，适合本系统规模)。
# 生产建议配合 systemd(见同目录 forklift-fault.service)。
set -e
cd "$(dirname "$0")/.."
exec .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
