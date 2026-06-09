from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QComboBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.services.import_export import ImportExportService
from src.services.repository import Repository
from src.utils.paths import EXPORTS_DIR


class ImportExportTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.repository = Repository()
        self.service = ImportExportService(self.repository)

        layout = QVBoxLayout(self)

        roster_group = QGroupBox("名单导入导出")
        roster_layout = QHBoxLayout(roster_group)
        export_roster_button = QPushButton("导出名单文件")
        export_roster_button.clicked.connect(self._export_roster_file)
        import_roster_button = QPushButton("导入名单文件")
        import_roster_button.clicked.connect(self._import_roster_file)
        roster_layout.addWidget(export_roster_button)
        roster_layout.addWidget(import_roster_button)
        layout.addWidget(roster_group)

        event_group = QGroupBox("活动班次字符串交换")
        event_layout = QGridLayout(event_group)
        self.shift_combo = QComboBox()
        self.shift_string_edit = QTextEdit()
        self.shift_string_edit.setPlaceholderText("导出的活动班次字符串 / 待导入字符串")
        export_shift_button = QPushButton("导出活动班次字符串")
        export_shift_button.clicked.connect(self._export_shift_string)
        import_shift_button = QPushButton("导入活动班次字符串")
        import_shift_button.clicked.connect(self._import_shift_string)
        event_layout.addWidget(QLabel("班次"), 0, 0)
        event_layout.addWidget(self.shift_combo, 0, 1)
        event_layout.addWidget(export_shift_button, 0, 2)
        event_layout.addWidget(import_shift_button, 0, 3)
        event_layout.addWidget(self.shift_string_edit, 1, 0, 1, 4)
        layout.addWidget(event_group)

        signup_group = QGroupBox("报名字符串交换")
        signup_layout = QGridLayout(signup_group)
        self.signup_shift_combo = QComboBox()
        self.signup_string_edit = QTextEdit()
        self.signup_string_edit.setPlaceholderText("导出的报名字符串 / 待导入字符串")
        export_signup_button = QPushButton("导出报名字符串")
        export_signup_button.clicked.connect(self._export_signup_string)
        import_signup_button = QPushButton("导入报名字符串")
        import_signup_button.clicked.connect(self._import_signup_string)
        signup_layout.addWidget(QLabel("目标班次"), 0, 0)
        signup_layout.addWidget(self.signup_shift_combo, 0, 1)
        signup_layout.addWidget(export_signup_button, 0, 2)
        signup_layout.addWidget(import_signup_button, 0, 3)
        signup_layout.addWidget(self.signup_string_edit, 1, 0, 1, 4)
        layout.addWidget(signup_group)

        assignment_group = QGroupBox("排班表导出")
        assignment_layout = QGridLayout(assignment_group)
        self.assignment_shift_combo = QComboBox()
        self.assignment_output_edit = QTextEdit()
        self.assignment_output_edit.setPlaceholderText("导出的排班 JSON / 字符串")
        export_assignment_json_button = QPushButton("导出排班文件")
        export_assignment_json_button.clicked.connect(self._export_assignment_file)
        export_assignment_string_button = QPushButton("导出排班字符串")
        export_assignment_string_button.clicked.connect(self._export_assignment_string)
        assignment_layout.addWidget(QLabel("班次"), 0, 0)
        assignment_layout.addWidget(self.assignment_shift_combo, 0, 1)
        assignment_layout.addWidget(export_assignment_json_button, 0, 2)
        assignment_layout.addWidget(export_assignment_string_button, 0, 3)
        assignment_layout.addWidget(self.assignment_output_edit, 1, 0, 1, 4)
        layout.addWidget(assignment_group)

        help_group = QGroupBox("使用说明")
        help_layout = QVBoxLayout(help_group)
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setPlainText(
            "1. 组织者先在‘活动与班次’创建活动、班次、模板。\n"
            "2. 在本页导出活动班次字符串，发送给其他人。\n"
            "3. 对方可在自己的客户端导入班次并报名，再导出报名字符串。\n"
            "4. 组织者导入报名字符串到目标班次。\n"
            "5. 在‘排班工作台’完成自动/手动排班。\n"
            "6. 在本页导出排班文件或排班字符串。"
        )
        help_layout.addWidget(help_text)
        layout.addWidget(help_group)

        self.refresh_choices()

    def refresh_choices(self) -> None:
        shift_items: list[tuple[str, int]] = []
        for event in self.repository.list_events():
            if event.id is None:
                continue
            for shift in self.repository.list_shifts_by_event(event.id):
                if shift.id is None:
                    continue
                label = f"{event.title} / {shift.shift_date} {shift.weekday_label} {shift.start_time}-{shift.end_time} (ID:{shift.id})"
                shift_items.append((label, shift.id))

        for combo in (self.shift_combo, self.signup_shift_combo, self.assignment_shift_combo):
            current = combo.currentData()
            combo.clear()
            for label, shift_id in shift_items:
                combo.addItem(label, shift_id)
            if current is not None:
                index = combo.findData(current)
                if index >= 0:
                    combo.setCurrentIndex(index)

    def _export_roster_file(self) -> None:
        payload = self.service.export_roster_payload()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出名单",
            str(EXPORTS_DIR / "roster.wrst_roster.json"),
            "Roster JSON (*.wrst_roster.json)",
        )
        if not file_path:
            return
        self.service.save_json_file(file_path, payload)
        QMessageBox.information(self, "完成", f"名单已导出到：{file_path}")

    def _import_roster_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "导入名单",
            str(EXPORTS_DIR),
            "Roster JSON (*.wrst_roster.json);;JSON (*.json)",
        )
        if not file_path:
            return
        payload = self.service.load_json_file(file_path)
        self.service.import_roster_payload(payload)
        QMessageBox.information(self, "完成", "名单导入完成。")

    def _export_shift_string(self) -> None:
        shift_id = self.shift_combo.currentData()
        if shift_id is None:
            QMessageBox.warning(self, "提示", "请先选择一个班次。")
            return
        try:
            payload = self.service.export_shift_payload(int(shift_id))
        except ValueError as exc:
            QMessageBox.warning(self, "提示", str(exc))
            return
        self.shift_string_edit.setPlainText(self.service.export_payload("event_shift", payload))

    def _import_shift_string(self) -> None:
        content = self.shift_string_edit.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "提示", "请输入活动班次字符串。")
            return
        envelope = self.service.import_payload(content)
        if envelope.get("payload_type") != "event_shift":
            QMessageBox.warning(self, "提示", "字符串类型不是活动班次。")
            return
        shift_id, _ = self.service.import_shift_payload(envelope["payload"])
        self.refresh_choices()
        QMessageBox.information(self, "完成", f"活动班次导入完成，班次 ID：{shift_id}")

    def _export_signup_string(self) -> None:
        shift_id = self.signup_shift_combo.currentData()
        if shift_id is None:
            QMessageBox.warning(self, "提示", "请先选择一个班次。")
            return
        payload = self.service.export_signups_payload(int(shift_id))
        self.signup_string_edit.setPlainText(self.service.export_payload("signups", payload))

    def _import_signup_string(self) -> None:
        shift_id = self.signup_shift_combo.currentData()
        if shift_id is None:
            QMessageBox.warning(self, "提示", "请先选择目标班次。")
            return
        content = self.signup_string_edit.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "提示", "请输入报名字符串。")
            return
        envelope = self.service.import_payload(content)
        if envelope.get("payload_type") != "signups":
            QMessageBox.warning(self, "提示", "字符串类型不是报名数据。")
            return
        self.service.import_signups_payload(int(shift_id), envelope["payload"])
        QMessageBox.information(self, "完成", "报名导入完成。")

    def _export_assignment_file(self) -> None:
        shift_id = self.assignment_shift_combo.currentData()
        if shift_id is None:
            QMessageBox.warning(self, "提示", "请先选择一个班次。")
            return
        payload = self.service.export_assignments_payload(int(shift_id))
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出排班表",
            str(EXPORTS_DIR / f"assignments_{shift_id}.wrst_schedule.json"),
            "Schedule JSON (*.wrst_schedule.json)",
        )
        if not file_path:
            return
        self.service.save_json_file(file_path, payload)
        self.assignment_output_edit.setPlainText(str(Path(file_path)))
        QMessageBox.information(self, "完成", f"排班表已导出到：{file_path}")

    def _export_assignment_string(self) -> None:
        shift_id = self.assignment_shift_combo.currentData()
        if shift_id is None:
            QMessageBox.warning(self, "提示", "请先选择一个班次。")
            return
        payload = self.service.export_assignments_payload(int(shift_id))
        self.assignment_output_edit.setPlainText(self.service.export_payload("assignments", payload))
