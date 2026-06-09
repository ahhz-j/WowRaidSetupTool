from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from src.domain.enums import CharacterClass, Role, ShiftStatus


@dataclass(slots=True)
class Person:
    id: int | None
    name: str
    note: str = ""
    default_available_days: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Character:
    id: int | None
    person_id: int
    name: str
    character_class: CharacterClass
    roles: List[Role] = field(default_factory=list)
    is_active: bool = True
    note: str = ""


@dataclass(slots=True)
class Template:
    id: int | None
    name: str
    tank_count: int
    healer_count: int
    dps_count: int
    note: str = ""


@dataclass(slots=True)
class Event:
    id: int | None
    title: str
    description: str = ""
    archived: bool = False


@dataclass(slots=True)
class EventShift:
    id: int | None
    event_id: int
    shift_date: str
    weekday_label: str
    start_time: str
    end_time: str
    template_id: int | None
    status: ShiftStatus = ShiftStatus.DRAFT
