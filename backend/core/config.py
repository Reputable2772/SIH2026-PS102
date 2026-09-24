"""
Backend Configuration for MPLADS Intelligence Platform.
"""

import os
from pathlib import Path

# Paths
BASE_DIR = Path(os.environ.get("MPLADS_BASE_DIR", str(Path(__file__).resolve().parent.parent.parent))).resolve()
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = BASE_DIR / "models"

# Security & Auth
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "mplads-sih-autonomous-core-secret-key-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Server Config
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))
DEBUG = os.environ.get("DEBUG", "true").lower() in ("true", "1")
