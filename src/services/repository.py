from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from src.domain.enums import CharacterClass, Role
from src.domain.models import Character, Person
from src.utils.paths import DB_PATH


class Repository:
    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path or str(DB_PATH)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def _serialize_days(days: list[str]) -> str:
        return ",".join(days)

    @staticmethod
    def _deserialize_days(value: str | None) -> list[str]:
        if not value:
            return []
        return [item for item in value.split(",") if item]

    @staticmethod
    def _serialize_roles(roles: list[Role]) -> str:
        return ",".join(role.value for role in roles)

    @staticmethod
    def _deserialize_roles(value: str) -> list[Role]:
        if not value:
            return []
        return [Role(item) for item in value.split(",") if item]

    def list_persons(self) -> list[Person]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT id, name, note, default_available_days FROM persons ORDER BY id"
            ).fetchall()
        return [
            Person(
                id=row["id"],
                name=row["name"],
                note=row["note"] or "",
                default_available_days=self._deserialize_days(row["default_available_days"]),
            )
            for row in rows
        ]

    def add_person(self, person: Person) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO persons(name, note, default_available_days) VALUES (?, ?, ?)",
                (person.name, person.note, self._serialize_days(person.default_available_days)),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def update_person(self, person: Person) -> None:
        if person.id is None:
            raise ValueError("person.id is required for update")
        with self.connect() as connection:
            connection.execute(
                "UPDATE persons SET name = ?, note = ?, default_available_days = ? WHERE id = ?",
                (
                    person.name,
                    person.note,
                    self._serialize_days(person.default_available_days),
                    person.id,
                ),
            )
            connection.commit()

    def delete_person(self, person_id: int) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM persons WHERE id = ?", (person_id,))
            connection.commit()

    def list_characters_by_person(self, person_id: int) -> list[Character]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT id, person_id, name, character_class, roles_csv, is_active, note "
                "FROM characters WHERE person_id = ? ORDER BY id",
                (person_id,),
            ).fetchall()
        return [
            Character(
                id=row["id"],
                person_id=row["person_id"],
                name=row["name"],
                character_class=CharacterClass(row["character_class"]),
                roles=self._deserialize_roles(row["roles_csv"]),
                is_active=bool(row["is_active"]),
                note=row["note"] or "",
            )
            for row in rows
        ]

    def add_character(self, character: Character) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO characters(person_id, name, character_class, roles_csv, is_active, note) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    character.person_id,
                    character.name,
                    character.character_class.value,
                    self._serialize_roles(character.roles),
                    int(character.is_active),
                    character.note,
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def update_character(self, character: Character) -> None:
        if character.id is None:
            raise ValueError("character.id is required for update")
        with self.connect() as connection:
            connection.execute(
                "UPDATE characters SET name = ?, character_class = ?, roles_csv = ?, is_active = ?, note = ? "
                "WHERE id = ?",
                (
                    character.name,
                    character.character_class.value,
                    self._serialize_roles(character.roles),
                    int(character.is_active),
                    character.note,
                    character.id,
                ),
            )
            connection.commit()

    def delete_character(self, character_id: int) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM characters WHERE id = ?", (character_id,))
            connection.commit()
