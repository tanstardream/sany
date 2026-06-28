"""FastAPI 入口。

启动时建表并初始化默认管理员账号(admin / admin123)。
CORS 放开所有来源：前端可托管在任意地址(如 GitHub Pages)，
后端地址由前端运行时选择，鉴权使用 Authorization 头(非 Cookie)。
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models, security  # noqa: F401  (注册模型 / 引入工具)
from .config import (
    CORS_ORIGINS,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_USERNAME,
)
from .database import Base, SessionLocal, engine
from .models.user import User
from .routers import auth, dicts, faults, forklifts, stats, upload, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(User).first():
            h, s = security.hash_password(DEFAULT_ADMIN_PASSWORD)
            db.add(
                User(
                    username=DEFAULT_ADMIN_USERNAME,
                    password_hash=h,
                    salt=s,
                    display_name="管理员",
                )
            )
            db.commit()
    finally:
        db.close()
    yield


app = FastAPI(title="叉车故障记录系统", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["系统"])
def health():
    return {"status": "ok"}


for _r in (auth, users, dicts, forklifts, faults, stats, upload):
    app.include_router(_r.router)
