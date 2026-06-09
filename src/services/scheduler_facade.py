from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from src.domain.enums import CharacterClass, Role
from src.domain.models import Assignment, Character, Event, EventShift, Person, Template
from src.services.buff_checker import BuffCheckResult, BuffCheckerService
from src.services.repository import Repository
from src.services.scheduler import SchedulerService


@dataclass(slots=True)
class AssignmentView:
    assignment: Assignment
    person: Person
    character: Character


@dataclass(slots=True)
class SchedulerSnapshot:
    events: list[Event]
    shifts_by_event: dict[int, list[EventShift]]
    templates_by_id: dict[int, Template]
    assignments_by_shift: dict[int, list[AssignmentView]]


@dataclass(slots=True)
class ScheduleStats:
    total: int
    tanks: int
    healers: int
    dps: int


class SchedulerFacade:
    def __init__(
        self,
        repository: Repository | None = None,
        scheduler_service: SchedulerService | None = None,
        buff_checker: BuffCheckerService | None = None,
    ) -> None:
        self.repository = repository or Repository()
        self.scheduler_service = scheduler_service or SchedulerService()
        self.buff_checker = buff_checker or BuffCheckerService()

    def get_snapshot(self) -> SchedulerSnapshot:
        events = self.repository.list_events()
        templates = self.repository.list_templates()
        templates_by_id = {template.id: template for template in templates if template.id is not None}
        persons = {person.id: person for person in self.repository.list_persons() if person.id is not None}
        characters_by_person = {
            person_id: self.repository.list_characters_by_person(person_id)
            for person_id in persons
        }
        characters_by_id = {
            character.id: character
            for items in characters_by_person.values()
            for character in items
            if character.id is not None
        }

        shifts_by_event: dict[int, list[EventShift]] = {}
        assignments_by_shift: dict[int, list[AssignmentView]] = {}
        for event in events:
            if event.id is None:
                continue
            shifts = self.repository.list_shifts_by_event(event.id)
            shifts_by_event[event.id] = shifts
            for shift in shifts:
                if shift.id is None:
                    continue
                assignment_views: list[AssignmentView] = []
                for assignment in self.repository.list_assignments_by_shift(shift.id):
                    person = persons.get(assignment.person_id)
                    character = characters_by_id.get(assignment.character_id)
                    if person is None or character is None:
                        continue
                    assignment_views.append(AssignmentView(assignment, person, character))
                assignments_by_shift[shift.id] = assignment_views

        return SchedulerSnapshot(
            events=events,
            shifts_by_event=shifts_by_event,
            templates_by_id=templates_by_id,
            assignments_by_shift=assignments_by_shift,
        )

    def auto_schedule(self, shift_id: int) -> None:
        shift = self._find_shift(shift_id)
        if shift is None or shift.template_id is None:
            raise ValueError("shift or template not found")
        template = self.repository.get_template(shift.template_id)
        if template is None:
            raise ValueError("template not found")

        persons = self.repository.list_persons()
        eligible_persons = [
            person for person in persons if shift.weekday_label in person.default_available_days
        ]
        if not eligible_persons:
            eligible_persons = persons

        characters_by_person = {
            person.id: self.repository.list_characters_by_person(person.id)
            for person in eligible_persons
            if person.id is not None
        }
        candidates = self.scheduler_service.build_schedule(eligible_persons, characters_by_person, template)
        assignments: list[Assignment] = []
        for index, candidate in enumerate(candidates, start=1):
            if candidate.person.id is None or candidate.character.id is None:
                continue
            assignments.append(
                Assignment(
                    id=None,
                    shift_id=shift_id,
                    person_id=candidate.person.id,
                    character_id=candidate.character.id,
                    role=candidate.role,
                    is_locked=False,
                    source="auto",
                    position_index=index,
                )
            )
        self.repository.replace_assignments(shift_id, assignments)

    def get_schedule_stats(self, assignment_views: list[AssignmentView]) -> ScheduleStats:
        counter = Counter(item.assignment.role for item in assignment_views)
        return ScheduleStats(
            total=len(assignment_views),
            tanks=counter[Role.TANK],
            healers=counter[Role.HEALER],
            dps=counter[Role.DPS],
        )

    def get_buff_results(self, assignment_views: list[AssignmentView]) -> list[BuffCheckResult]:
        classes = [item.character.character_class for item in assignment_views]
        return self.buff_checker.evaluate(classes)

    def _find_shift(self, shift_id: int) -> EventShift | None:
        for event in self.repository.list_events():
            if event.id is None:
                continue
            for shift in self.repository.list_shifts_by_event(event.id):
                if shift.id == shift_id:
                    return shift
        return None
