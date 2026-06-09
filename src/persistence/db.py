from __future__ import annotations

import sqlite3

from src.persistence.schema_loader import load_schema
from src.utils.paths import DB_PATH


def initialize_database() -> None:
    connection = sqlite3.connect(DB_PATH)
    try:
        connection.executescript(load_schema())
        connection.commit()
    finally:
        connection.close()
