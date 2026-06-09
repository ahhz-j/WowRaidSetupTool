from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.domain.enums import ShiftStatus
from src.domain.models import Event, EventShift, Template
from src.services.event_service import EventService
from src.services.repository import Repository


class EventsTab(QWidget):
    WEEKDAY_OPTIONS = [
        ("Fri", 4),
        ("Sat", 5),
        ("Sun", 6),
        ("Mon", 0),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.repository = Repository()
        self.event_service = EventService(self.repository)
        self.selected_event_id: int | None = None
        self.selected_shift_id: int | None = None
        self.events_by_id: dict[int, Event] = {}
        self.shifts_by_id: dict[int, EventShift] = {}
        self.templates_by_id: dict[int, Template] = {}

        root = QHBoxLayout(self)

        left = QVBoxLayout()
        left.addWidget(QLabel("活动列表"))
        self.event_list = QListWidget()
        self.event_list.currentItemChanged.connect(self._on_event_selected)
        left.addWidget(self.event_list)

        event_buttons = QHBoxLayout()
        add_event_button = QPushButton("新增活动")
        add_event_button.clicked.connect(self._add_event)
        delete_event_button = QPushButton("删除活动")
        delete_event_button.clicked.connect(self._delete_event)
        event_buttons.addWidget(add_event_button)
        event_buttons.addWidget(delete_event_button)
        left.addLayout(event_buttons)
        root.addLayout(left, 2)

        middle = QVBoxLayout()
        event_group = QGroupBox("活动详情")
        event_form = QFormLayout(event_group)
        self.event_title_edit = QLineEdit()
        self.event_description_edit = QTextEdit()
        self.event_description_edit.setFixedHeight(80)
        self.event_archived_check = QCheckBox("归档")
        self.save_event_button = QPushButton("保存活动")
        self.save_event_button.clicked.connect(self._save_event)

        event_form.addRow("标题", self.event_title_edit)
        event_form.addRow("说明", self.event_description_edit)
        event_form.addRow("状态", self.event_archived_check)
        event_form.addRow(self.save_event_button)
        middle.addWidget(event_group)

        shift_group = QGroupBox("班次列表与详情")
        shift_layout = QVBoxLayout(shift_group)
        self.shift_list = QListWidget()
        self.shift_list.currentItemChanged.connect(self._on_shift_selected)
        shift_layout.addWidget(self.shift_list)

        shift_buttons = QHBoxLayout()
        add_shift_button = QPushButton("新增班次")
        add_shift_button.clicked.connect(self._add_shift)
        delete_shift_button = QPushButton("删除班次")
        delete_shift_button.clicked.connect(self._delete_shift)
        batch_button = QPushButton("批量生成周五/六/日/一")
        batch_button.clicked.connect(self._batch_generate_shifts)
        shift_buttons.addWidget(add_shift_button)
        shift_buttons.addWidget(delete_shift_button)
        shift_buttons.addWidget(batch_button)
        shift_layout.addLayout(shift_buttons)

        shift_form = QFormLayout()
        self.shift_date_edit = QLineEdit()
        self.shift_weekday_combo = QComboBox()
        for label, _ in self.WEEKDAY_OPTIONS:
            self.shift_weekday_combo.addItem(label)
        self.shift_start_edit = QLineEdit()
        self.shift_end_edit = QLineEdit()
        self.shift_template_combo = QComboBox()
        self.shift_status_combo = QComboBox()
        for status in ShiftStatus:
            self.shift_status_combo.addItem(status.value, status)
        self.save_shift_button = QPushButton("保存班次")
        self.save_shift_button.clicked.connect(self._save_shift)

        shift_form.addRow("日期 (YYYY-MM-DD)", self.shift_date_edit)
        shift_form.addRow("星期", self.shift_weekday_combo)
        shift_form.addRow("开始时间", self.shift_start_edit)
        shift_form.addRow("结束时间", self.shift_end_edit)
        shift_form.addRow("阵容模板", self.shift_template_combo)
        shift_form.addRow("状态", self.shift_status_combo)
        shift_form.addRow(self.save_shift_button)
        shift_layout.addLayout(shift_form)

        batch_group = QGroupBox("批量生成设置")
        batch_form = QFormLayout(batch_group)
        self.batch_start_date_edit = QLineEdit()
        self.batch_start_date_edit.setPlaceholderText("例如 2026-06-12")
        self.batch_start_time_edit = QLineEdit("20:00")
        self.batch_end_time_edit = QLineEdit("23:30")
        batch_form.addRow("起始日期", self.batch_start_date_edit)
        batch_form.addRow("默认开始时间", self.batch_start_time_edit)
        batch_form.addRow("默认结束时间", self.batch_end_time_edit)
        middle.addWidget(shift_group)
        middle.addWidget(batch_group)

        root.addLayout(middle, 3)

        self.refresh_data()

    def refresh_data(self) -> None:
        snapshot = self.event_service.get_snapshot()
        self.events_by_id = {event.id: event for event in snapshot.events if event.id is not None}
        self.templates_by_id = {template.id: template for template in snapshot.templates if template.id is not None}
        self.event_list.clear()
        self._reload_template_combo()

        for event in snapshot.events:
            if event.id is None:
                continue
            suffix = "[归档]" if event.archived else ""
            item = QListWidgetItem(f"{event.title} {suffix}".strip())
            item.setData(Qt.ItemDataRole.UserRole, event.id)
            self.event_list.addItem(item)

        if self.selected_event_id is not None:
            self._select_event_item(self.selected_event_id)
        elif self.event_list.count() == 0:
            self._clear_event_form()
            self._clear_shift_form()
            self.shift_list.clear()

    def _reload_template_combo(self) -> None:
        current_template_id = self.shift_template_combo.currentData()
        self.shift_template_combo.clear()
        self.shift_template_combo.addItem("未指定", None)
        for template in self.templates_by_id.values():
            if template.id is None:
                continue
            self.shift_template_combo.addItem(
                f"{template.name} ({template.tank_count}/{template.healer_count}/{template.dps_count})",
                template.id,
            )
        if current_template_id is not None:
            index = self.shift_template_combo.findData(current_template_id)
            if index >= 0:
                self.shift_template_combo.setCurrentIndex(index)

    def _select_event_item(self, event_id: int) -> None:
        for index in range(self.event_list.count()):
            item = self.event_list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == event_id:
                self.event_list.setCurrentItem(item)
                return

    def _on_event_selected(self, current: QListWidgetItem | None, _: QListWidgetItem | None) -> None:
        if current is None:
            self.selected_event_id = None
            self._clear_event_form()
            self.shift_list.clear()
            self._clear_shift_form()
            return
        event_id = current.data(Qt.ItemDataRole.UserRole)
        self.selected_event_id = event_id
        event = self.events_by_id[event_id]
        self.event_title_edit.setText(event.title)
        self.event_description_edit.setPlainText(event.description)
        self.event_archived_check.setChecked(event.archived)
        self._load_shifts(event_id)

    def _load_shifts(self, event_id: int) -> None:
        shifts = self.repository.list_shifts_by_event(event_id)
        self.shift_list.clear()
        self.shifts_by_id = {shift.id: shift for shift in shifts if shift.id is not None}
        for shift in shifts:
            if shift.id is None:
                continue
            template_name = self.templates_by_id.get(shift.template_id).name if shift.template_id in self.templates_by_id else "无模板"
            item = QListWidgetItem(
                f"{shift.shift_date} {shift.weekday_label} {shift.start_time}-{shift.end_time} [{template_name}]"
            )
            item.setData(Qt.ItemDataRole.UserRole, shift.id)
            self.shift_list.addItem(item)
        self.selected_shift_id = None
        self._clear_shift_form()

    def _on_shift_selected(self, current: QListWidgetItem | None, _: QListWidgetItem | None) -> None:
        if current is None:
            self.selected_shift_id = None
            self._clear_shift_form()
            return
        shift_id = current.data(Qt.ItemDataRole.UserRole)
        self.selected_shift_id = shift_id
        shift = self.shifts_by_id[shift_id]
        self.shift_date_edit.setText(shift.shift_date)
        self.shift_weekday_combo.setCurrentIndex(self.shift_weekday_combo.findText(shift.weekday_label))
        self.shift_start_edit.setText(shift.start_time)
        self.shift_end_edit.setText(shift.end_time)
        template_index = self.shift_template_combo.findData(shift.template_id)
        self.shift_template_combo.setCurrentIndex(template_index if template_index >= 0 else 0)
        status_index = self.shift_status_combo.findData(shift.status)
        self.shift_status_combo.setCurrentIndex(status_index if status_index >= 0 else 0)

    def _save_event(self) -> None:
        title = self.event_title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "提示", "活动标题不能为空。")
            return
        event = Event(
            id=self.selected_event_id,
            title=title,
            description=self.event_description_edit.toPlainText().strip(),
            archived=self.event_archived_check.isChecked(),
        )
        if self.selected_event_id is None:
            self.selected_event_id = self.repository.add_event(event)
        else:
            self.repository.update_event(event)
        self.refresh_data()

    def _add_event(self) -> None:
        self.selected_event_id = None
        self._clear_event_form()
        self.shift_list.clear()
        self._clear_shift_form()
        self.event_list.clearSelection()

    def _delete_event(self) -> None:
        if self.selected_event_id is None:
            return
        result = QMessageBox.question(self, "确认", "删除活动会同时删除其班次，是否继续？")
        if result != QMessageBox.StandardButton.Yes:
            return
        self.repository.delete_event(self.selected_event_id)
        self.selected_event_id = None
        self.refresh_data()

    def _save_shift(self) -> None:
        if self.selected_event_id is None:
            QMessageBox.warning(self, "提示", "请先选择或保存一个活动。")
            return
        shift_date = self.shift_date_edit.text().strip()
        if not shift_date:
            QMessageBox.warning(self, "提示", "班次日期不能为空。")
            return
        shift = EventShift(
            id=self.selected_shift_id,
            event_id=self.selected_event_id,
            shift_date=shift_date,
            weekday_label=self.shift_weekday_combo.currentText(),
            start_time=self.shift_start_edit.text().strip() or "20:00",
            end_time=self.shift_end_edit.text().strip() or "23:30",
            template_id=self.shift_template_combo.currentData(),
            status=self.shift_status_combo.currentData(),
        )
        if self.selected_shift_id is None:
            self.selected_shift_id = self.repository.add_shift(shift)
        else:
            self.repository.update_shift(shift)
        self._load_shifts(self.selected_event_id)

    def _add_shift(self) -> None:
        if self.selected_event_id is None:
            QMessageBox.warning(self, "提示", "请先选择一个活动。")
            return
        self.selected_shift_id = None
        self._clear_shift_form()
        self.shift_list.clearSelection()

    def _delete_shift(self) -> None:
        if self.selected_shift_id is None:
            return
        result = QMessageBox.question(self, "确认", "确定删除当前班次吗？")
        if result != QMessageBox.StandardButton.Yes:
            return
        self.repository.delete_shift(self.selected_shift_id)
        self.selected_shift_id = None
        if self.selected_event_id is not None:
            self._load_shifts(self.selected_event_id)

    def _batch_generate_shifts(self) -> None:
        if self.selected_event_id is None:
            QMessageBox.warning(self, "提示", "请先选择一个活动。")
            return
        start_date_text = self.batch_start_date_edit.text().strip()
        if not start_date_text:
            QMessageBox.warning(self, "提示", "请填写起始日期。")
            return
        try:
            start = date.fromisoformat(start_date_text)
        except ValueError:
            QMessageBox.warning(self, "提示", "起始日期格式应为 YYYY-MM-DD。")
            return

        created = 0
        for offset in range(14):
            current = start + timedelta(days=offset)
            weekday = current.weekday()
            for label, weekday_number in self.WEEKDAY_OPTIONS:
                if weekday == weekday_number:
                    shift = EventShift(
                        id=None,
                        event_id=self.selected_event_id,
                        shift_date=current.isoformat(),
                        weekday_label=label,
                        start_time=self.batch_start_time_edit.text().strip() or "20:00",
                        end_time=self.batch_end_time_edit.text().strip() or "23:30",
                        template_id=self.shift_template_combo.currentData(),
                        status=ShiftStatus.OPEN,
                    )
                    self.repository.add_shift(shift)
                    created += 1
                    break
        self._load_shifts(self.selected_event_id)
        QMessageBox.information(self, "完成", f"已批量生成 {created} 个班次。")

    def _clear_event_form(self) -> None:
        self.event_title_edit.clear()
        self.event_description_edit.clear()
        self.event_archived_check.setChecked(False)

    def _clear_shift_form(self) -> None:
        self.shift_date_edit.clear()
        self.shift_weekday_combo.setCurrentIndex(0)
        self.shift_start_edit.setText("20:00")
        self.shift_end_edit.setText("23:30")
        self.shift_template_combo.setCurrentIndex(0)
        self.shift_status_combo.setCurrentIndex(0)
