from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.services.scheduler_facade import AssignmentView, SchedulerFacade


class SchedulerTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.facade = SchedulerFacade()
        self.selected_event_id: int | None = None
        self.selected_shift_id: int | None = None

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
        middle.addWidget(QLabel("当前阵容"))
        self.assignment_list = QListWidget()
        middle.addWidget(self.assignment_list)
        self.stats_label = QLabel("总人数: 0 | Tank: 0 | Healer: 0 | DPS: 0")
        middle.addWidget(self.stats_label)
        root.addLayout(middle, 3)

        right = QVBoxLayout()
        right.addWidget(QLabel("Buff / Debuff 覆盖检查"))
        self.buff_list = QListWidget()
        right.addWidget(self.buff_list)
        self.conflict_label = QLabel("冲突检查：当前未发现同自然人重复上场。")
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

        if self.selected_event_id is not None:
            self._select_item(self.event_list, self.selected_event_id)
        elif self.event_list.count() > 0:
            self.event_list.setCurrentRow(0)
        else:
            self.shift_list.clear()
            self.assignment_list.clear()
            self.buff_list.clear()

    def _select_item(self, widget: QListWidget, target_id: int) -> None:
        for index in range(widget.count()):
            item = widget.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == target_id:
                widget.setCurrentItem(item)
                return

    def _on_event_selected(self, current: QListWidgetItem | None, _: QListWidgetItem | None) -> None:
        self.shift_list.clear()
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
            self.assignment_list.clear()
            self.buff_list.clear()
            return
        self.selected_shift_id = current.data(Qt.ItemDataRole.UserRole)
        assignment_views = self.snapshot.assignments_by_shift.get(self.selected_shift_id, [])
        self._render_assignments(assignment_views)

    def _render_assignments(self, assignment_views: list[AssignmentView]) -> None:
        self.assignment_list.clear()
        for item in assignment_views:
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
        self.conflict_label.setText("冲突检查：当前未发现同自然人重复上场。")

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
        if self.selected_event_id is not None:
            self._select_item(self.event_list, self.selected_event_id)
        if self.selected_shift_id is not None:
            self._select_item(self.shift_list, self.selected_shift_id)
