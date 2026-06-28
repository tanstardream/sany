"""应用配置。所有敏感值应通过环境变量覆盖。"""
import os
from pathlib import Path

# backend/
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# SQLite 数据库文件
DB_PATH = DATA_DIR / "forklift.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# JWT
JWT_SECRET = os.getenv("JWT_SECRET", "forklift-fault-dev-secret-change-me")
JWT_ALGO = "HS256"
JWT_EXP_HOURS = int(os.getenv("JWT_EXP_HOURS", "24"))

# 允许的前端来源：前端可托管在任意地址（GitHub Pages / 内网静态服务器），
# 且后端地址由前端运行时选择，因此放开所有来源。鉴权使用 Authorization 头（非 Cookie），
# 所以允许通配来源不会触发带凭据(Credentials)的 CORS 限制。
CORS_ORIGINS = ["*"]

# 首次启动自动初始化的默认管理员账号
DEFAULT_ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
