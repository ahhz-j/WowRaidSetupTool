from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
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

from src.domain.models import Template
from src.services.repository import Repository


class TemplatesTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.repository = Repository()
        self.selected_template_id: int | None = None
        self.templates_by_id: dict[int, Template] = {}

        root = QHBoxLayout(self)

        left = QVBoxLayout()
        left.addWidget(QLabel("模板列表"))
        self.template_list = QListWidget()
        self.template_list.currentItemChanged.connect(self._on_template_selected)
        left.addWidget(self.template_list)

        button_row = QHBoxLayout()
        add_button = QPushButton("新增模板")
        add_button.clicked.connect(self._add_template)
        delete_button = QPushButton("删除模板")
        delete_button.clicked.connect(self._delete_template)
        button_row.addWidget(add_button)
        button_row.addWidget(delete_button)
        left.addLayout(button_row)

        root.addLayout(left, 2)

        group = QGroupBox("模板详情")
        form = QFormLayout(group)
        self.name_edit = QLineEdit()
        self.tank_edit = QLineEdit()
        self.healer_edit = QLineEdit()
        self.dps_edit = QLineEdit()
        self.note_edit = QTextEdit()
        self.note_edit.setFixedHeight(120)

        form.addRow("模板名称", self.name_edit)
        form.addRow("Tank 数量", self.tank_edit)
        form.addRow("Healer 数量", self.healer_edit)
        form.addRow("DPS 数量", self.dps_edit)
        form.addRow("备注", self.note_edit)

        self.save_button = QPushButton("保存模板")
        self.save_button.clicked.connect(self._save_template)
        form.addRow(self.save_button)

        root.addWidget(group, 3)

        self.refresh_data()

    def refresh_data(self) -> None:
        templates = self.repository.list_templates()
        self.templates_by_id = {template.id: template for template in templates if template.id is not None}
        self.template_list.clear()
        for template in templates:
            if template.id is None:
                continue
            item = QListWidgetItem(f"{template.name} ({template.tank_count}/{template.healer_count}/{template.dps_count})")
            item.setData(Qt.ItemDataRole.UserRole, template.id)
            self.template_list.addItem(item)
        if self.selected_template_id is not None:
            self._select_template_item(self.selected_template_id)
        elif self.template_list.count() == 0:
            self._clear_form()

    def _select_template_item(self, template_id: int) -> None:
        for index in range(self.template_list.count()):
            item = self.template_list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == template_id:
                self.template_list.setCurrentItem(item)
                return

    def _on_template_selected(self, current: QListWidgetItem | None, _: QListWidgetItem | None) -> None:
        if current is None:
            self.selected_template_id = None
            self._clear_form()
            return
        template_id = current.data(Qt.ItemDataRole.UserRole)
        self.selected_template_id = template_id
        template = self.templates_by_id[template_id]
        self.name_edit.setText(template.name)
        self.tank_edit.setText(str(template.tank_count))
        self.healer_edit.setText(str(template.healer_count))
        self.dps_edit.setText(str(template.dps_count))
        self.note_edit.setPlainText(template.note)

    def _save_template(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "模板名称不能为空。")
            return
        try:
            tank = int(self.tank_edit.text().strip())
            healer = int(self.healer_edit.text().strip())
            dps = int(self.dps_edit.text().strip())
        except ValueError:
            QMessageBox.warning(self, "提示", "Tank / Healer / DPS 必须是整数。")
            return
        if tank + healer + dps != 25:
            QMessageBox.warning(self, "提示", "模板总人数必须等于 25。")
            return
        template = Template(
            id=self.selected_template_id,
            name=name,
            tank_count=tank,
            healer_count=healer,
            dps_count=dps,
            note=self.note_edit.toPlainText().strip(),
        )
        if self.selected_template_id is None:
            self.selected_template_id = self.repository.add_template(template)
        else:
            self.repository.update_template(template)
        self.refresh_data()

    def _add_template(self) -> None:
        self.selected_template_id = None
        self._clear_form()
        self.template_list.clearSelection()

    def _delete_template(self) -> None:
        if self.selected_template_id is None:
            return
        result = QMessageBox.question(self, "确认", "确定删除当前模板吗？")
        if result != QMessageBox.StandardButton.Yes:
            return
        self.repository.delete_template(self.selected_template_id)
        self.selected_template_id = None
        self.refresh_data()

    def _clear_form(self) -> None:
        self.name_edit.clear()
        self.tank_edit.setText("2")
        self.healer_edit.setText("5")
        self.dps_edit.setText("18")
        self.note_edit.clear()
