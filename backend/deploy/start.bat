@echo off
REM 本地开发启动后端（带热重载）
cd /d "%~dp0\.."
.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload
