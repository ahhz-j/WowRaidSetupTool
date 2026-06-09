from __future__ import annotations

from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = APP_ROOT / "data"
EXPORTS_DIR = DATA_DIR / "exports"
BACKUPS_DIR = DATA_DIR / "backups"
LOGS_DIR = DATA_DIR / "logs"
DB_PATH = DATA_DIR / "app.db"


def ensure_directories() -> None:
    for path in (DATA_DIR, EXPORTS_DIR, BACKUPS_DIR, LOGS_DIR):
        path.mkdir(parents=True, exist_ok=True)
