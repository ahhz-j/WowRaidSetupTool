from __future__ import annotations

from dataclasses import dataclass

from src.domain.models import Character, Person
from src.services.repository import Repository


@dataclass(slots=True)
class RosterSnapshot:
    persons: list[Person]
    characters_by_person: dict[int, list[Character]]


class RosterService:
    def __init__(self, repository: Repository | None = None) -> None:
        self.repository = repository or Repository()

    def get_snapshot(self) -> RosterSnapshot:
        persons = self.repository.list_persons()
        characters_by_person = {
            person.id: self.repository.list_characters_by_person(person.id)
            for person in persons
            if person.id is not None
        }
        return RosterSnapshot(persons=persons, characters_by_person=characters_by_person)
