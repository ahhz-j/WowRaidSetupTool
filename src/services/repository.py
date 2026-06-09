from __future__ import annotations

import sqlite3
from dataclasses import asdict
from typing import Iterable

from src.domain.models import Person
from src.utils.paths import DB_PATH


class Repository:
    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path or str(DB_PATH)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def list_persons(self) -> list[Person]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT id, name, note FROM persons ORDER BY id"
            ).fetchall()
        return [Person(id=row["id"], name=row["name"], note=row["note"] or "") for row in rows]

    def add_person(self, person: Person) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO persons(name, note) VALUES (?, ?)",
                (person.name, person.note),
            )
            connection.commit()
            return int(cursor.lastrowid)
