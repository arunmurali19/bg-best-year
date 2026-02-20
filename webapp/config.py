"""Flask app configuration."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    DATABASE = str(BASE_DIR / "webapp" / "tournament.db")
    ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "admin123")
