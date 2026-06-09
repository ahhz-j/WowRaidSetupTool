from __future__ import annotations

import sqlite3

from src.persistence.schema_loader import load_schema
from src.utils.paths import DB_PATH


def _column_names(connection: sqlite3.Connection, table_name: str) -> set[str]:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row[1] for row in rows}


def _apply_migrations(connection: sqlite3.Connection) -> None:
    person_columns = _column_names(connection, "persons")
    if "default_available_days" not in person_columns:
        connection.execute(
            "ALTER TABLE persons ADD COLUMN default_available_days TEXT NOT NULL DEFAULT ''"
        )

    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }

    if "signups" not in tables:
        connection.execute(
            """
            CREATE TABLE signups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shift_id INTEGER NOT NULL,
                person_id INTEGER NOT NULL,
                character_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'signed',
                source TEXT NOT NULL DEFAULT 'manual',
                note TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (shift_id) REFERENCES event_shifts(id) ON DELETE CASCADE,
                FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE,
                FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
            )
            """
        )

    if "assignments" not in tables:
        connection.execute(
            """
            CREATE TABLE assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shift_id INTEGER NOT NULL,
                person_id INTEGER NOT NULL,
                character_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                is_locked INTEGER NOT NULL DEFAULT 0,
                source TEXT NOT NULL DEFAULT 'auto',
                position_index INTEGER NOT NULL DEFAULT 0,
                UNIQUE(shift_id, person_id),
                UNIQUE(shift_id, character_id),
                FOREIGN KEY (shift_id) REFERENCES event_shifts(id) ON DELETE CASCADE,
                FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE,
                FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
            )
            """
        )


def initialize_database() -> None:
    connection = sqlite3.connect(DB_PATH)
    try:
        connection.executescript(load_schema())
        _apply_migrations(connection)
        connection.commit()
    finally:
        connection.close()
