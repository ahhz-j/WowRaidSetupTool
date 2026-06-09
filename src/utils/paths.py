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


def ensure_sample_export_files() -> None:
    readme_path = EXPORTS_DIR / "README.txt"
    if not readme_path.exists():
        readme_path.write_text(
            "导出文件会保存在这里。\n"
            "推荐扩展名：\n"
            "- .wrst_roster.json 名单\n"
            "- .wrst_event.json 活动/班次\n"
            "- .wrst_schedule.json 排班\n",
            encoding="utf-8",
        )
