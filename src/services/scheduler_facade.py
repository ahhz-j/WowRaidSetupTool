from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from src.domain.enums import Role
from src.domain.models import Assignment, Character, Event, EventShift, Person, Signup, Template
from src.services.buff_checker import BuffCheckResult, BuffCheckerService
from src.services.repository import Repository
from src.services.scheduler import Candidate, SchedulerService


@dataclass(slots=True)
class SignupView:
    signup: Signup
    person: Person
    character: Character


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
    signups_by_shift: dict[int, list[SignupView]]
    assignments_by_shift: dict[int, list[AssignmentView]]
    persons_by_id: dict[int, Person]
    characters_by_id: dict[int, Character]


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
        persons_by_id = {person.id: person for person in self.repository.list_persons() if person.id is not None}
        all_characters = self.repository.list_all_characters()
        characters_by_id = {character.id: character for character in all_characters if character.id is not None}

        shifts_by_event: dict[int, list[EventShift]] = {}
        signups_by_shift: dict[int, list[SignupView]] = {}
        assignments_by_shift: dict[int, list[AssignmentView]] = {}
        for event in events:
            if event.id is None:
                continue
            shifts = self.repository.list_shifts_by_event(event.id)
            shifts_by_event[event.id] = shifts
            for shift in shifts:
                if shift.id is None:
                    continue
                signups: list[SignupView] = []
                for signup in self.repository.list_signups_by_shift(shift.id):
                    person = persons_by_id.get(signup.person_id)
                    character = characters_by_id.get(signup.character_id)
                    if person is None or character is None:
                        continue
                    signups.append(SignupView(signup, person, character))
                signups_by_shift[shift.id] = signups

                assignment_views: list[AssignmentView] = []
                for assignment in self.repository.list_assignments_by_shift(shift.id):
                    person = persons_by_id.get(assignment.person_id)
                    character = characters_by_id.get(assignment.character_id)
                    if person is None or character is None:
                        continue
                    assignment_views.append(AssignmentView(assignment, person, character))
                assignments_by_shift[shift.id] = assignment_views

        return SchedulerSnapshot(
            events=events,
            shifts_by_event=shifts_by_event,
            templates_by_id=templates_by_id,
            signups_by_shift=signups_by_shift,
            assignments_by_shift=assignments_by_shift,
            persons_by_id=persons_by_id,
            characters_by_id=characters_by_id,
        )

    def auto_schedule(self, shift_id: int) -> None:
        shift = self._find_shift(shift_id)
        if shift is None or shift.template_id is None:
            raise ValueError("shift or template not found")
        template = self.repository.get_template(shift.template_id)
        if template is None:
            raise ValueError("template not found")

        existing = self.repository.list_assignments_by_shift(shift_id)
        locked_assignments = [item for item in existing if item.is_locked]
        locked_person_ids = {item.person_id for item in locked_assignments}

        signup_map = self.repository.list_signups_by_shift(shift_id)
        if signup_map:
            persons_by_id = {person.id: person for person in self.repository.list_persons() if person.id is not None}
            characters_by_person: dict[int, list[Character]] = {}
            eligible_persons: list[Person] = []
            for signup in signup_map:
                if signup.person_id in locked_person_ids:
                    continue
                person = persons_by_id.get(signup.person_id)
                if person is None:
                    continue
                if person not in eligible_persons:
                    eligible_persons.append(person)
                character = self.repository.list_all_characters()
                for item in character:
                    if item.id == signup.character_id:
                        characters_by_person.setdefault(signup.person_id, []).append(item)
                        break
        else:
            persons = self.repository.list_persons()
            eligible_persons = [
                person for person in persons if shift.weekday_label in person.default_available_days and person.id not in locked_person_ids
            ]
            if not eligible_persons:
                eligible_persons = [person for person in persons if person.id not in locked_person_ids]
            characters_by_person = {
                person.id: self.repository.list_characters_by_person(person.id)
                for person in eligible_persons
                if person.id is not None
            }

        candidates = self.scheduler_service.build_schedule(eligible_persons, characters_by_person, template)
        assignments = [
            Assignment(
                id=item.id,
                shift_id=item.shift_id,
                person_id=item.person_id,
                character_id=item.character_id,
                role=item.role,
                is_locked=item.is_locked,
                source=item.source,
                position_index=item.position_index,
            )
            for item in locked_assignments
        ]
        used_person_ids = {item.person_id for item in assignments}
        used_character_ids = {item.character_id for item in assignments}

        next_position = len(assignments) + 1
        for candidate in candidates:
            if candidate.person.id is None or candidate.character.id is None:
                continue
            if candidate.person.id in used_person_ids or candidate.character.id in used_character_ids:
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
                    position_index=next_position,
                )
            )
            used_person_ids.add(candidate.person.id)
            used_character_ids.add(candidate.character.id)
            next_position += 1

        self.repository.replace_assignments(shift_id, assignments[:25])

    def add_manual_signup(self, shift_id: int, person_id: int, character_id: int, role: Role) -> None:
        signup = Signup(
            id=None,
            shift_id=shift_id,
            person_id=person_id,
            character_id=character_id,
            role=role,
            status="signed",
            source="manual",
            note="",
        )
        self.repository.add_signup(signup)

    def remove_signup(self, signup_id: int) -> None:
        self.repository.delete_signup(signup_id)

    def add_assignment_from_signup(self, shift_id: int, signup_id: int) -> None:
        signups = self.repository.list_signups_by_shift(shift_id)
        target = next((item for item in signups if item.id == signup_id), None)
        if target is None:
            raise ValueError("signup not found")
        existing = self.repository.list_assignments_by_shift(shift_id)
        if any(item.person_id == target.person_id for item in existing):
            raise ValueError("该自然人已在当前排班中")
        if any(item.character_id == target.character_id for item in existing):
            raise ValueError("该角色已在当前排班中")
        assignment = Assignment(
            id=None,
            shift_id=shift_id,
            person_id=target.person_id,
            character_id=target.character_id,
            role=target.role,
            is_locked=False,
            source="manual",
            position_index=len(existing) + 1,
        )
        self.repository.save_assignment(assignment)

    def remove_assignment(self, assignment_id: int) -> None:
        self.repository.delete_assignment(assignment_id)

    def toggle_assignment_lock(self, assignment_id: int, is_locked: bool) -> None:
        self.repository.update_assignment_lock(assignment_id, is_locked)

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

    def get_conflicts(self, assignment_views: list[AssignmentView]) -> list[str]:
        conflicts: list[str] = []
        person_counter = Counter(item.person.id for item in assignment_views)
        for item in assignment_views:
            if item.person.id is not None and person_counter[item.person.id] > 1:
                conflicts.append(f"自然人 {item.person.name} 重复上场")
        return sorted(set(conflicts))

    def _find_shift(self, shift_id: int) -> EventShift | None:
        for event in self.repository.list_events():
            if event.id is None:
                continue
            for shift in self.repository.list_shifts_by_event(event.id):
                if shift.id == shift_id:
                    return shift
        return None
