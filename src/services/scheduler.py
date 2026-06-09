from __future__ import annotations

from dataclasses import dataclass

from src.domain.enums import Role


@dataclass(slots=True)
class Candidate:
    person_name: str
    character_name: str
    role: Role
    score: int


class SchedulerService:
    """Initial placeholder scheduler service.

    This version returns an empty list and will be replaced by
    rule-based scheduling logic in a later iteration.
    """

    def build_schedule(self) -> list[Candidate]:
        return []
