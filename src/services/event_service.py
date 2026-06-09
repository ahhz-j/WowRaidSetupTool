from __future__ import annotations

from dataclasses import dataclass

from src.domain.models import Event, EventShift, Template
from src.services.repository import Repository


@dataclass(slots=True)
class EventSnapshot:
    events: list[Event]
    templates: list[Template]
    shifts_by_event: dict[int, list[EventShift]]


class EventService:
    def __init__(self, repository: Repository | None = None) -> None:
        self.repository = repository or Repository()

    def get_snapshot(self) -> EventSnapshot:
        events = self.repository.list_events()
        templates = self.repository.list_templates()
        shifts_by_event = {
            event.id: self.repository.list_shifts_by_event(event.id)
            for event in events
            if event.id is not None
        }
        return EventSnapshot(events=events, templates=templates, shifts_by_event=shifts_by_event)
