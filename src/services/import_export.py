from __future__ import annotations

import base64
import json
import zlib
from pathlib import Path
from typing import Any

from src.domain.enums import CharacterClass, Role, ShiftStatus
from src.domain.models import Assignment, Character, Event, EventShift, Person, Signup, Template
from src.services.repository import Repository
from src.utils.serialize import to_plain_data


class ImportExportService:
    PROTOCOL_VERSION = 1

    def __init__(self, repository: Repository | None = None) -> None:
        self.repository = repository or Repository()

    def export_payload(self, payload_type: str, payload: dict[str, Any]) -> str:
        envelope = {
            "protocol_version": self.PROTOCOL_VERSION,
            "payload_type": payload_type,
            "payload": payload,
        }
        raw = json.dumps(envelope, ensure_ascii=False).encode("utf-8")
        compressed = zlib.compress(raw)
        return base64.b64encode(compressed).decode("ascii")

    def import_payload(self, content: str) -> dict[str, Any]:
        compressed = base64.b64decode(content.encode("ascii"))
        raw = zlib.decompress(compressed)
        return json.loads(raw.decode("utf-8"))

    def _find_person_by_name(self, name: str) -> Person | None:
        for person in self.repository.list_persons():
            if person.name == name:
                return person
        return None

    def _find_character(self, person_id: int, name: str, character_class: CharacterClass) -> Character | None:
        for character in self.repository.list_characters_by_person(person_id):
            if character.name == name and character.character_class == character_class:
                return character
        return None

    def _find_template_by_name(self, name: str) -> Template | None:
        for template in self.repository.list_templates():
            if template.name == name:
                return template
        return None

    def _find_event_by_title(self, title: str) -> Event | None:
        for event in self.repository.list_events():
            if event.title == title:
                return event
        return None

    def export_roster_payload(self) -> dict[str, Any]:
        persons = self.repository.list_persons()
        characters = self.repository.list_all_characters()
        return {
            "persons": to_plain_data(persons),
            "characters": to_plain_data(characters),
        }

    def import_roster_payload(self, payload: dict[str, Any]) -> None:
        person_id_map: dict[int, int] = {}
        for person_data in payload.get("persons", []):
            existing = self._find_person_by_name(person_data["name"])
            if existing is not None and existing.id is not None:
                person_id_map[int(person_data.get("id") or 0)] = existing.id
                continue
            person = Person(
                id=None,
                name=person_data["name"],
                note=person_data.get("note", ""),
                default_available_days=person_data.get("default_available_days", []),
            )
            new_id = self.repository.add_person(person)
            old_id = int(person_data.get("id") or 0)
            if old_id:
                person_id_map[old_id] = new_id

        for character_data in payload.get("characters", []):
            old_person_id = int(character_data["person_id"])
            new_person_id = person_id_map.get(old_person_id)
            if new_person_id is None:
                continue
            character_class = CharacterClass(character_data["character_class"])
            existing_character = self._find_character(new_person_id, character_data["name"], character_class)
            if existing_character is not None:
                continue
            character = Character(
                id=None,
                person_id=new_person_id,
                name=character_data["name"],
                character_class=character_class,
                roles=[Role(item) for item in character_data.get("roles", [])],
                is_active=bool(character_data.get("is_active", True)),
                note=character_data.get("note", ""),
            )
            self.repository.add_character(character)

    def export_events_payload(self) -> dict[str, Any]:
        events = self.repository.list_events()
        shifts: list[EventShift] = []
        for event in events:
            if event.id is None:
                continue
            shifts.extend(self.repository.list_shifts_by_event(event.id))
        templates = self.repository.list_templates()
        return {
            "events": to_plain_data(events),
            "shifts": to_plain_data(shifts),
            "templates": to_plain_data(templates),
        }

    def export_shift_payload(self, shift_id: int) -> dict[str, Any]:
        events = self.repository.list_events()
        for event in events:
            if event.id is None:
                continue
            for shift in self.repository.list_shifts_by_event(event.id):
                if shift.id == shift_id:
                    template = self.repository.get_template(shift.template_id) if shift.template_id else None
                    return {
                        "event": to_plain_data(event),
                        "shift": to_plain_data(shift),
                        "template": to_plain_data(template) if template else None,
                    }
        raise ValueError("shift not found")

    def import_shift_payload(self, payload: dict[str, Any]) -> tuple[int, int | None]:
        template_data = payload.get("template")
        template_id: int | None = None
        if template_data:
            existing_template = self._find_template_by_name(template_data["name"])
            if existing_template is not None:
                template_id = existing_template.id
            else:
                template = Template(
                    id=None,
                    name=template_data["name"],
                    tank_count=int(template_data["tank_count"]),
                    healer_count=int(template_data["healer_count"]),
                    dps_count=int(template_data["dps_count"]),
                    note=template_data.get("note", ""),
                )
                template_id = self.repository.add_template(template)

        event_data = payload["event"]
        existing_event = self._find_event_by_title(event_data["title"])
        if existing_event is not None and existing_event.id is not None:
            event_id = existing_event.id
        else:
            event = Event(
                id=None,
                title=event_data["title"],
                description=event_data.get("description", ""),
                archived=bool(event_data.get("archived", False)),
            )
            event_id = self.repository.add_event(event)

        shift_data = payload["shift"]
        existing_shifts = self.repository.list_shifts_by_event(event_id)
        for item in existing_shifts:
            if (
                item.shift_date == shift_data["shift_date"]
                and item.start_time == shift_data["start_time"]
                and item.end_time == shift_data["end_time"]
            ):
                return item.id or 0, item.template_id

        shift = EventShift(
            id=None,
            event_id=event_id,
            shift_date=shift_data["shift_date"],
            weekday_label=shift_data["weekday_label"],
            start_time=shift_data["start_time"],
            end_time=shift_data["end_time"],
            template_id=template_id,
            status=ShiftStatus(shift_data["status"]),
        )
        shift_id = self.repository.add_shift(shift)
        return shift_id, template_id

    def export_signups_payload(self, shift_id: int) -> dict[str, Any]:
        signups = self.repository.list_signups_by_shift(shift_id)
        persons = {person.id: person for person in self.repository.list_persons() if person.id is not None}
        characters = {character.id: character for character in self.repository.list_all_characters() if character.id is not None}
        related_persons = []
        related_characters = []
        seen_person_ids: set[int] = set()
        seen_character_ids: set[int] = set()
        for signup in signups:
            if signup.person_id in persons and signup.person_id not in seen_person_ids:
                related_persons.append(persons[signup.person_id])
                seen_person_ids.add(signup.person_id)
            if signup.character_id in characters and signup.character_id not in seen_character_ids:
                related_characters.append(characters[signup.character_id])
                seen_character_ids.add(signup.character_id)
        return {
            "shift_id": shift_id,
            "persons": to_plain_data(related_persons),
            "characters": to_plain_data(related_characters),
            "signups": to_plain_data(signups),
        }

    def import_signups_payload(self, target_shift_id: int, payload: dict[str, Any]) -> None:
        person_id_map: dict[int, int] = {}
        for person_data in payload.get("persons", []):
            existing = self._find_person_by_name(person_data["name"])
            if existing is not None and existing.id is not None:
                person_id_map[int(person_data.get("id") or 0)] = existing.id
                continue
            person = Person(
                id=None,
                name=person_data["name"],
                note=person_data.get("note", ""),
                default_available_days=person_data.get("default_available_days", []),
            )
            new_id = self.repository.add_person(person)
            old_id = int(person_data.get("id") or 0)
            if old_id:
                person_id_map[old_id] = new_id

        character_id_map: dict[int, int] = {}
        for character_data in payload.get("characters", []):
            old_person_id = int(character_data["person_id"])
            new_person_id = person_id_map.get(old_person_id)
            if new_person_id is None:
                continue
            character_class = CharacterClass(character_data["character_class"])
            existing_character = self._find_character(new_person_id, character_data["name"], character_class)
            if existing_character is not None and existing_character.id is not None:
                character_id_map[int(character_data.get("id") or 0)] = existing_character.id
                continue
            character = Character(
                id=None,
                person_id=new_person_id,
                name=character_data["name"],
                character_class=character_class,
                roles=[Role(item) for item in character_data.get("roles", [])],
                is_active=bool(character_data.get("is_active", True)),
                note=character_data.get("note", ""),
            )
            new_character_id = self.repository.add_character(character)
            old_character_id = int(character_data.get("id") or 0)
            if old_character_id:
                character_id_map[old_character_id] = new_character_id

        existing_signups = self.repository.list_signups_by_shift(target_shift_id)
        existing_pairs = {(item.person_id, item.character_id, item.role.value) for item in existing_signups}
        for signup_data in payload.get("signups", []):
            old_person_id = int(signup_data["person_id"])
            old_character_id = int(signup_data["character_id"])
            new_person_id = person_id_map.get(old_person_id)
            new_character_id = character_id_map.get(old_character_id)
            if new_person_id is None or new_character_id is None:
                continue
            pair = (new_person_id, new_character_id, signup_data["role"])
            if pair in existing_pairs:
                continue
            signup = Signup(
                id=None,
                shift_id=target_shift_id,
                person_id=new_person_id,
                character_id=new_character_id,
                role=Role(signup_data["role"]),
                status=signup_data.get("status", "signed"),
                source=signup_data.get("source", "imported"),
                note=signup_data.get("note", ""),
            )
            self.repository.add_signup(signup)
            existing_pairs.add(pair)

    def export_assignments_payload(self, shift_id: int) -> dict[str, Any]:
        assignments = self.repository.list_assignments_by_shift(shift_id)
        persons = {person.id: person for person in self.repository.list_persons() if person.id is not None}
        characters = {character.id: character for character in self.repository.list_all_characters() if character.id is not None}
        related_persons = []
        related_characters = []
        seen_person_ids: set[int] = set()
        seen_character_ids: set[int] = set()
        for assignment in assignments:
            if assignment.person_id in persons and assignment.person_id not in seen_person_ids:
                related_persons.append(persons[assignment.person_id])
                seen_person_ids.add(assignment.person_id)
            if assignment.character_id in characters and assignment.character_id not in seen_character_ids:
                related_characters.append(characters[assignment.character_id])
                seen_character_ids.add(assignment.character_id)
        return {
            "shift_id": shift_id,
            "persons": to_plain_data(related_persons),
            "characters": to_plain_data(related_characters),
            "assignments": to_plain_data(assignments),
        }

    def save_json_file(self, path: str | Path, payload: dict[str, Any]) -> None:
        Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_json_file(self, path: str | Path) -> dict[str, Any]:
        return json.loads(Path(path).read_text(encoding="utf-8"))
