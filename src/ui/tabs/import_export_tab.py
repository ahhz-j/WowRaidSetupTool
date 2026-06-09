from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
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
        self.shift_id_edit = QLineEdit()
        self.shift_id_edit.setPlaceholderText("输入班次 ID")
        self.shift_string_edit = QTextEdit()
        self.shift_string_edit.setPlaceholderText("导出的活动班次字符串 / 待导入字符串")
        export_shift_button = QPushButton("导出活动班次字符串")
        export_shift_button.clicked.connect(self._export_shift_string)
        import_shift_button = QPushButton("导入活动班次字符串")
        import_shift_button.clicked.connect(self._import_shift_string)
        event_layout.addWidget(QLabel("班次 ID"), 0, 0)
        event_layout.addWidget(self.shift_id_edit, 0, 1)
        event_layout.addWidget(export_shift_button, 0, 2)
        event_layout.addWidget(import_shift_button, 0, 3)
        event_layout.addWidget(self.shift_string_edit, 1, 0, 1, 4)
        layout.addWidget(event_group)

        signup_group = QGroupBox("报名字符串交换")
        signup_layout = QGridLayout(signup_group)
        self.signup_target_shift_id_edit = QLineEdit()
        self.signup_target_shift_id_edit.setPlaceholderText("导入时目标班次 ID / 导出时来源班次 ID")
        self.signup_string_edit = QTextEdit()
        self.signup_string_edit.setPlaceholderText("导出的报名字符串 / 待导入字符串")
        export_signup_button = QPushButton("导出报名字符串")
        export_signup_button.clicked.connect(self._export_signup_string)
        import_signup_button = QPushButton("导入报名字符串")
        import_signup_button.clicked.connect(self._import_signup_string)
        signup_layout.addWidget(QLabel("班次 ID"), 0, 0)
        signup_layout.addWidget(self.signup_target_shift_id_edit, 0, 1)
        signup_layout.addWidget(export_signup_button, 0, 2)
        signup_layout.addWidget(import_signup_button, 0, 3)
        signup_layout.addWidget(self.signup_string_edit, 1, 0, 1, 4)
        layout.addWidget(signup_group)

        assignment_group = QGroupBox("排班表导出")
        assignment_layout = QGridLayout(assignment_group)
        self.assignment_shift_id_edit = QLineEdit()
        self.assignment_shift_id_edit.setPlaceholderText("输入班次 ID")
        self.assignment_output_edit = QTextEdit()
        self.assignment_output_edit.setPlaceholderText("导出的排班 JSON / 字符串")
        export_assignment_json_button = QPushButton("导出排班文件")
        export_assignment_json_button.clicked.connect(self._export_assignment_file)
        export_assignment_string_button = QPushButton("导出排班字符串")
        export_assignment_string_button.clicked.connect(self._export_assignment_string)
        assignment_layout.addWidget(QLabel("班次 ID"), 0, 0)
        assignment_layout.addWidget(self.assignment_shift_id_edit, 0, 1)
        assignment_layout.addWidget(export_assignment_json_button, 0, 2)
        assignment_layout.addWidget(export_assignment_string_button, 0, 3)
        assignment_layout.addWidget(self.assignment_output_edit, 1, 0, 1, 4)
        layout.addWidget(assignment_group)

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
        shift_id = self._parse_int(self.shift_id_edit.text())
        if shift_id is None:
            return
        try:
            payload = self.service.export_shift_payload(shift_id)
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
        QMessageBox.information(self, "完成", f"活动班次导入完成，新班次 ID：{shift_id}")

    def _export_signup_string(self) -> None:
        shift_id = self._parse_int(self.signup_target_shift_id_edit.text())
        if shift_id is None:
            return
        payload = self.service.export_signups_payload(shift_id)
        self.signup_string_edit.setPlainText(self.service.export_payload("signups", payload))

    def _import_signup_string(self) -> None:
        shift_id = self._parse_int(self.signup_target_shift_id_edit.text())
        if shift_id is None:
            return
        content = self.signup_string_edit.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "提示", "请输入报名字符串。")
            return
        envelope = self.service.import_payload(content)
        if envelope.get("payload_type") != "signups":
            QMessageBox.warning(self, "提示", "字符串类型不是报名数据。")
            return
        self.service.import_signups_payload(shift_id, envelope["payload"])
        QMessageBox.information(self, "完成", "报名导入完成。")

    def _export_assignment_file(self) -> None:
        shift_id = self._parse_int(self.assignment_shift_id_edit.text())
        if shift_id is None:
            return
        payload = self.service.export_assignments_payload(shift_id)
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
        shift_id = self._parse_int(self.assignment_shift_id_edit.text())
        if shift_id is None:
            return
        payload = self.service.export_assignments_payload(shift_id)
        self.assignment_output_edit.setPlainText(self.service.export_payload("assignments", payload))

    def _parse_int(self, value: str) -> int | None:
        value = value.strip()
        if not value:
            QMessageBox.warning(self, "提示", "请输入有效 ID。")
            return None
        try:
            return int(value)
        except ValueError:
            QMessageBox.warning(self, "提示", "ID 必须是整数。")
            return None
