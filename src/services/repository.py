from __future__ import annotations

import sqlite3

from src.domain.enums import CharacterClass, Role, ShiftStatus
from src.domain.models import Assignment, Character, Event, EventShift, Person, Template
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

    def list_templates(self) -> list[Template]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT id, name, tank_count, healer_count, dps_count, note FROM templates ORDER BY id"
            ).fetchall()
        return [
            Template(
                id=row["id"],
                name=row["name"],
                tank_count=row["tank_count"],
                healer_count=row["healer_count"],
                dps_count=row["dps_count"],
                note=row["note"] or "",
            )
            for row in rows
        ]

    def get_template(self, template_id: int) -> Template | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT id, name, tank_count, healer_count, dps_count, note FROM templates WHERE id = ?",
                (template_id,),
            ).fetchone()
        if row is None:
            return None
        return Template(
            id=row["id"],
            name=row["name"],
            tank_count=row["tank_count"],
            healer_count=row["healer_count"],
            dps_count=row["dps_count"],
            note=row["note"] or "",
        )

    def add_template(self, template: Template) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO templates(name, tank_count, healer_count, dps_count, note) VALUES (?, ?, ?, ?, ?)",
                (template.name, template.tank_count, template.healer_count, template.dps_count, template.note),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def update_template(self, template: Template) -> None:
        if template.id is None:
            raise ValueError("template.id is required for update")
        with self.connect() as connection:
            connection.execute(
                "UPDATE templates SET name = ?, tank_count = ?, healer_count = ?, dps_count = ?, note = ? WHERE id = ?",
                (template.name, template.tank_count, template.healer_count, template.dps_count, template.note, template.id),
            )
            connection.commit()

    def delete_template(self, template_id: int) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM templates WHERE id = ?", (template_id,))
            connection.commit()

    def list_events(self) -> list[Event]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT id, title, description, archived FROM events ORDER BY id DESC"
            ).fetchall()
        return [
            Event(
                id=row["id"],
                title=row["title"],
                description=row["description"] or "",
                archived=bool(row["archived"]),
            )
            for row in rows
        ]

    def add_event(self, event: Event) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO events(title, description, archived) VALUES (?, ?, ?)",
                (event.title, event.description, int(event.archived)),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def update_event(self, event: Event) -> None:
        if event.id is None:
            raise ValueError("event.id is required for update")
        with self.connect() as connection:
            connection.execute(
                "UPDATE events SET title = ?, description = ?, archived = ? WHERE id = ?",
                (event.title, event.description, int(event.archived), event.id),
            )
            connection.commit()

    def delete_event(self, event_id: int) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM events WHERE id = ?", (event_id,))
            connection.commit()

    def list_shifts_by_event(self, event_id: int) -> list[EventShift]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT id, event_id, shift_date, weekday_label, start_time, end_time, template_id, status "
                "FROM event_shifts WHERE event_id = ? ORDER BY shift_date, start_time, id",
                (event_id,),
            ).fetchall()
        return [
            EventShift(
                id=row["id"],
                event_id=row["event_id"],
                shift_date=row["shift_date"],
                weekday_label=row["weekday_label"],
                start_time=row["start_time"],
                end_time=row["end_time"],
                template_id=row["template_id"],
                status=ShiftStatus(row["status"]),
            )
            for row in rows
        ]

    def add_shift(self, shift: EventShift) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO event_shifts(event_id, shift_date, weekday_label, start_time, end_time, template_id, status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    shift.event_id,
                    shift.shift_date,
                    shift.weekday_label,
                    shift.start_time,
                    shift.end_time,
                    shift.template_id,
                    shift.status.value,
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def update_shift(self, shift: EventShift) -> None:
        if shift.id is None:
            raise ValueError("shift.id is required for update")
        with self.connect() as connection:
            connection.execute(
                "UPDATE event_shifts SET shift_date = ?, weekday_label = ?, start_time = ?, end_time = ?, template_id = ?, status = ? "
                "WHERE id = ?",
                (
                    shift.shift_date,
                    shift.weekday_label,
                    shift.start_time,
                    shift.end_time,
                    shift.template_id,
                    shift.status.value,
                    shift.id,
                ),
            )
            connection.commit()

    def delete_shift(self, shift_id: int) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM event_shifts WHERE id = ?", (shift_id,))
            connection.commit()

    def list_assignments_by_shift(self, shift_id: int) -> list[Assignment]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT id, shift_id, person_id, character_id, role, is_locked, source, position_index "
                "FROM assignments WHERE shift_id = ? ORDER BY position_index, id",
                (shift_id,),
            ).fetchall()
        return [
            Assignment(
                id=row["id"],
                shift_id=row["shift_id"],
                person_id=row["person_id"],
                character_id=row["character_id"],
                role=Role(row["role"]),
                is_locked=bool(row["is_locked"]),
                source=row["source"],
                position_index=row["position_index"],
            )
            for row in rows
        ]

    def replace_assignments(self, shift_id: int, assignments: list[Assignment]) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM assignments WHERE shift_id = ?", (shift_id,))
            for index, assignment in enumerate(assignments, start=1):
                connection.execute(
                    "INSERT INTO assignments(shift_id, person_id, character_id, role, is_locked, source, position_index) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        shift_id,
                        assignment.person_id,
                        assignment.character_id,
                        assignment.role.value,
                        int(assignment.is_locked),
                        assignment.source,
                        index,
                    ),
                )
            connection.commit()
