from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.domain.enums import Role
from src.services.scheduler_facade import AssignmentView, SchedulerFacade


class SchedulerTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.facade = SchedulerFacade()
        self.selected_event_id: int | None = None
        self.selected_shift_id: int | None = None
        self.current_assignment_ids: list[int] = []
        self.current_signup_ids: list[int] = []

        root = QHBoxLayout(self)

        left = QVBoxLayout()
        left.addWidget(QLabel("活动"))
        self.event_list = QListWidget()
        self.event_list.currentItemChanged.connect(self._on_event_selected)
        left.addWidget(self.event_list)

        left.addWidget(QLabel("班次"))
        self.shift_list = QListWidget()
        self.shift_list.currentItemChanged.connect(self._on_shift_selected)
        left.addWidget(self.shift_list)

        self.auto_button = QPushButton("自动排班")
        self.auto_button.clicked.connect(self._auto_schedule)
        left.addWidget(self.auto_button)

        root.addLayout(left, 2)

        middle = QVBoxLayout()
        middle.addWidget(QLabel("报名池 / 预分配池"))
        self.signup_list = QListWidget()
        middle.addWidget(self.signup_list)

        signup_controls = QHBoxLayout()
        self.signup_character_combo = QComboBox()
        self.signup_role_combo = QComboBox()
        for role in Role:
            self.signup_role_combo.addItem(role.value, role)
        self.add_signup_button = QPushButton("添加报名")
        self.add_signup_button.clicked.connect(self._add_signup)
        self.import_signup_button = QPushButton("加入排班")
        self.import_signup_button.clicked.connect(self._promote_signup_to_assignment)
        self.remove_signup_button = QPushButton("移除报名")
        self.remove_signup_button.clicked.connect(self._remove_signup)
        signup_controls.addWidget(self.signup_character_combo)
        signup_controls.addWidget(self.signup_role_combo)
        signup_controls.addWidget(self.add_signup_button)
        signup_controls.addWidget(self.import_signup_button)
        signup_controls.addWidget(self.remove_signup_button)
        middle.addLayout(signup_controls)

        middle.addWidget(QLabel("当前阵容"))
        self.assignment_list = QListWidget()
        middle.addWidget(self.assignment_list)

        assignment_controls = QHBoxLayout()
        self.remove_assignment_button = QPushButton("移除排班")
        self.remove_assignment_button.clicked.connect(self._remove_assignment)
        self.lock_assignment_button = QPushButton("切换锁定")
        self.lock_assignment_button.clicked.connect(self._toggle_lock)
        assignment_controls.addWidget(self.remove_assignment_button)
        assignment_controls.addWidget(self.lock_assignment_button)
        middle.addLayout(assignment_controls)

        self.stats_label = QLabel("总人数: 0 | Tank: 0 | Healer: 0 | DPS: 0")
        middle.addWidget(self.stats_label)
        root.addLayout(middle, 4)

        right = QVBoxLayout()
        right.addWidget(QLabel("Buff / Debuff 覆盖检查"))
        self.buff_list = QListWidget()
        right.addWidget(self.buff_list)
        self.conflict_label = QLabel("冲突检查：当前未发现冲突。")
        right.addWidget(self.conflict_label)
        root.addLayout(right, 3)

        self.refresh_data()

    def refresh_data(self) -> None:
        snapshot = self.facade.get_snapshot()
        self.snapshot = snapshot
        self.event_list.clear()
        for event in snapshot.events:
            if event.id is None:
                continue
            item = QListWidgetItem(event.title)
            item.setData(Qt.ItemDataRole.UserRole, event.id)
            self.event_list.addItem(item)

        self._reload_signup_character_combo()

        if self.selected_event_id is not None:
            self._select_item(self.event_list, self.selected_event_id)
        elif self.event_list.count() > 0:
            self.event_list.setCurrentRow(0)
        else:
            self.shift_list.clear()
            self.signup_list.clear()
            self.assignment_list.clear()
            self.buff_list.clear()

    def _reload_signup_character_combo(self) -> None:
        self.signup_character_combo.clear()
        for character in self.snapshot.characters_by_id.values():
            if character.id is None or not character.is_active:
                continue
            person = self.snapshot.persons_by_id.get(character.person_id)
            if person is None:
                continue
            self.signup_character_combo.addItem(
                f"{person.name} - {character.name} - {character.character_class.value}",
                (person.id, character.id),
            )

    def _select_item(self, widget: QListWidget, target_id: int) -> None:
        for index in range(widget.count()):
            item = widget.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == target_id:
                widget.setCurrentItem(item)
                return

    def _on_event_selected(self, current: QListWidgetItem | None, _: QListWidgetItem | None) -> None:
        self.shift_list.clear()
        self.signup_list.clear()
        self.assignment_list.clear()
        self.buff_list.clear()
        if current is None:
            self.selected_event_id = None
            return
        event_id = current.data(Qt.ItemDataRole.UserRole)
        self.selected_event_id = event_id
        for shift in self.snapshot.shifts_by_event.get(event_id, []):
            if shift.id is None:
                continue
            template = self.snapshot.templates_by_id.get(shift.template_id)
            template_name = template.name if template else "无模板"
            item = QListWidgetItem(f"{shift.shift_date} {shift.weekday_label} [{template_name}]")
            item.setData(Qt.ItemDataRole.UserRole, shift.id)
            self.shift_list.addItem(item)
        if self.shift_list.count() > 0:
            self.shift_list.setCurrentRow(0)

    def _on_shift_selected(self, current: QListWidgetItem | None, _: QListWidgetItem | None) -> None:
        if current is None:
            self.selected_shift_id = None
            self.signup_list.clear()
            self.assignment_list.clear()
            self.buff_list.clear()
            return
        self.selected_shift_id = current.data(Qt.ItemDataRole.UserRole)
        self._render_shift_state()

    def _render_shift_state(self) -> None:
        if self.selected_shift_id is None:
            return
        signup_views = self.snapshot.signups_by_shift.get(self.selected_shift_id, [])
        assignment_views = self.snapshot.assignments_by_shift.get(self.selected_shift_id, [])

        self.signup_list.clear()
        self.current_signup_ids = []
        for item in signup_views:
            signup_id = item.signup.id
            if signup_id is None:
                continue
            self.current_signup_ids.append(signup_id)
            self.signup_list.addItem(
                f"{item.person.name} - {item.character.name} - {item.character.character_class.value} - {item.signup.role.value}"
            )

        self.assignment_list.clear()
        self.current_assignment_ids = []
        for item in assignment_views:
            assignment_id = item.assignment.id
            if assignment_id is None:
                continue
            self.current_assignment_ids.append(assignment_id)
            locked = "锁定" if item.assignment.is_locked else item.assignment.source
            self.assignment_list.addItem(
                f"{item.person.name} - {item.character.name} - {item.character.character_class.value} - {item.assignment.role.value} ({locked})"
            )

        stats = self.facade.get_schedule_stats(assignment_views)
        self.stats_label.setText(
            f"总人数: {stats.total} | Tank: {stats.tanks} | Healer: {stats.healers} | DPS: {stats.dps}"
        )
        buff_results = self.facade.get_buff_results(assignment_views)
        self.buff_list.clear()
        for result in buff_results:
            status = "已覆盖" if result.covered else "缺失"
            self.buff_list.addItem(f"[{result.category}] {result.name}: {status}")
        conflicts = self.facade.get_conflicts(assignment_views)
        if conflicts:
            self.conflict_label.setText("冲突检查：" + "；".join(conflicts))
        else:
            self.conflict_label.setText("冲突检查：当前未发现冲突。")

    def _add_signup(self) -> None:
        if self.selected_shift_id is None:
            QMessageBox.warning(self, "提示", "��先选择一个班次。")
            return
        data = self.signup_character_combo.currentData()
        if data is None:
            QMessageBox.warning(self, "提示", "没有可用角色可报名。")
            return
        person_id, character_id = data
        role = self.signup_role_combo.currentData()
        self.facade.add_manual_signup(self.selected_shift_id, person_id, character_id, role)
        self.refresh_data()
        self._restore_selection()

    def _promote_signup_to_assignment(self) -> None:
        if self.selected_shift_id is None:
            return
        row = self.signup_list.currentRow()
        if row < 0 or row >= len(self.current_signup_ids):
            QMessageBox.warning(self, "提示", "请先选择一个报名项。")
            return
        signup_id = self.current_signup_ids[row]
        try:
            self.facade.add_assignment_from_signup(self.selected_shift_id, signup_id)
        except ValueError as exc:
            QMessageBox.warning(self, "提示", str(exc))
            return
        self.refresh_data()
        self._restore_selection()

    def _remove_signup(self) -> None:
        row = self.signup_list.currentRow()
        if row < 0 or row >= len(self.current_signup_ids):
            return
        self.facade.remove_signup(self.current_signup_ids[row])
        self.refresh_data()
        self._restore_selection()

    def _remove_assignment(self) -> None:
        row = self.assignment_list.currentRow()
        if row < 0 or row >= len(self.current_assignment_ids):
            return
        self.facade.remove_assignment(self.current_assignment_ids[row])
        self.refresh_data()
        self._restore_selection()

    def _toggle_lock(self) -> None:
        row = self.assignment_list.currentRow()
        if row < 0 or row >= len(self.current_assignment_ids):
            return
        assignment_id = self.current_assignment_ids[row]
        views = self.snapshot.assignments_by_shift.get(self.selected_shift_id, []) if self.selected_shift_id is not None else []
        for item in views:
            if item.assignment.id == assignment_id:
                self.facade.toggle_assignment_lock(assignment_id, not item.assignment.is_locked)
                break
        self.refresh_data()
        self._restore_selection()

    def _auto_schedule(self) -> None:
        if self.selected_shift_id is None:
            QMessageBox.warning(self, "提示", "请先选择一个班次。")
            return
        try:
            self.facade.auto_schedule(self.selected_shift_id)
        except ValueError as exc:
            QMessageBox.warning(self, "提示", str(exc))
            return
        self.refresh_data()
        self._restore_selection()

    def _restore_selection(self) -> None:
        if self.selected_event_id is not None:
            self._select_item(self.event_list, self.selected_event_id)
        if self.selected_shift_id is not None:
            self._select_item(self.shift_list, self.selected_shift_id)
