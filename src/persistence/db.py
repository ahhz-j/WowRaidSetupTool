from __future__ import annotations

import sqlite3

from src.persistence.schema_loader import load_schema
from src.utils.paths import DB_PATH


def _apply_migrations(connection: sqlite3.Connection) -> None:
    table_info = connection.execute("PRAGMA table_info(persons)").fetchall()
    columns = {row[1] for row in table_info}
    if "default_available_days" not in columns:
        connection.execute(
            "ALTER TABLE persons ADD COLUMN default_available_days TEXT NOT NULL DEFAULT ''"
        )


def initialize_database() -> None:
    connection = sqlite3.connect(DB_PATH)
    try:
        connection.executescript(load_schema())
        _apply_migrations(connection)
        connection.commit()
    finally:
        connection.close()
