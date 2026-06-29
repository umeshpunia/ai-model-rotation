"""Pytest configuration and shared fixtures for the AI Gateway Pro test suite."""
from __future__ import annotations
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault(
    "DATABASE_URL",
    "mysql+pymysql://root:@localhost:3306/aigateway_test?charset=utf8mb4",
)
os.environ.setdefault(
    "SECRET_KEY",
    "test-secret-key-please-change-32-chars-min-aaaaaaaaaaa",
)
os.environ.setdefault("MASTER_PASSWORD_SALT", "test-salt-value-12-chars")
os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ.setdefault("LOG_FORMAT", "console")
os.environ.setdefault("LOG_DIR", "./logs_test")
os.environ.setdefault("SCHEDULER_ENABLED", "false")
os.environ.setdefault("RELOAD", "false")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault(
    "CORS_ORIGINS",
    '["http://localhost:5173","http://localhost:8080"]',
)
