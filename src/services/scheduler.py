from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from src.domain.enums import Role
from src.domain.models import Character, Person, Template


@dataclass(slots=True)
class Candidate:
    person: Person
    character: Character
    role: Role
    score: int


class SchedulerService:
    """Rule-based initial scheduler implementation."""

    ROLE_PRIORITY = {
        Role.TANK: 3,
        Role.HEALER: 2,
        Role.DPS: 1,
    }

    def build_schedule(
        self,
        persons: list[Person],
        characters_by_person: dict[int, list[Character]],
        template: Template,
    ) -> list[Candidate]:
        selected_person_ids: set[int] = set()
        assignments: list[Candidate] = []

        role_targets = [
            (Role.TANK, template.tank_count),
            (Role.HEALER, template.healer_count),
            (Role.DPS, template.dps_count),
        ]

        for role, target in role_targets:
            pool = self._build_candidate_pool(persons, characters_by_person, role, selected_person_ids)
            for candidate in pool[:target]:
                if candidate.person.id is None:
                    continue
                assignments.append(candidate)
                selected_person_ids.add(candidate.person.id)

        return assignments[:25]

    def _build_candidate_pool(
        self,
        persons: list[Person],
        characters_by_person: dict[int, list[Character]],
        target_role: Role,
        selected_person_ids: set[int],
    ) -> list[Candidate]:
        candidates: list[Candidate] = []
        for person in persons:
            if person.id is None or person.id in selected_person_ids:
                continue
            for character in characters_by_person.get(person.id, []):
                if not character.is_active:
                    continue
                if target_role not in character.roles:
                    continue
                score = self._score_character(character, target_role)
                candidates.append(
                    Candidate(
                        person=person,
                        character=character,
                        role=target_role,
                        score=score,
                    )
                )
        return sorted(
            candidates,
            key=lambda item: (
                -item.score,
                item.person.name.lower(),
                item.character.name.lower(),
            ),
        )

    def _score_character(self, character: Character, target_role: Role) -> int:
        score = self.ROLE_PRIORITY[target_role] * 100
        score += len(character.roles) * 5
        score += 10 if character.roles and character.roles[0] == target_role else 0
        return score
