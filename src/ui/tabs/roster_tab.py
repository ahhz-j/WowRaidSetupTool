from __future__ import annotations

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

from src.domain.enums import CharacterClass, Role
from src.domain.models import Character, Person
from src.services.repository import Repository
from src.services.roster_service import RosterService


class RosterTab(QWidget):
    DAY_OPTIONS = ["Fri", "Sat", "Sun", "Mon"]

    def __init__(self) -> None:
        super().__init__()
        self.repository = Repository()
        self.roster_service = RosterService(self.repository)
        self.selected_person_id: int | None = None
        self.selected_character_id: int | None = None
        self.persons_by_id: dict[int, Person] = {}
        self.characters_by_id: dict[int, Character] = {}

        root = QHBoxLayout(self)

        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("自然人列表"))
        self.person_list = QListWidget()
        self.person_list.currentItemChanged.connect(self._on_person_selected)
        left_panel.addWidget(self.person_list)

        person_button_row = QHBoxLayout()
        self.add_person_button = QPushButton("新增自然人")
        self.add_person_button.clicked.connect(self._add_person)
        self.delete_person_button = QPushButton("删除自然人")
        self.delete_person_button.clicked.connect(self._delete_person)
        person_button_row.addWidget(self.add_person_button)
        person_button_row.addWidget(self.delete_person_button)
        left_panel.addLayout(person_button_row)

        root.addLayout(left_panel, 2)

        middle_panel = QVBoxLayout()
        person_group = QGroupBox("自然人详情")
        person_form = QFormLayout(person_group)
        self.person_name_edit = QLineEdit()
        self.person_note_edit = QTextEdit()
        self.person_note_edit.setFixedHeight(80)

        self.day_checks: dict[str, QCheckBox] = {}
        day_layout = QHBoxLayout()
        for day in self.DAY_OPTIONS:
            checkbox = QCheckBox(day)
            self.day_checks[day] = checkbox
            day_layout.addWidget(checkbox)

        person_form.addRow("昵称", self.person_name_edit)
        person_form.addRow("默认可参加", self._wrap_layout(day_layout))
        person_form.addRow("备注", self.person_note_edit)

        self.save_person_button = QPushButton("保存自然人")
        self.save_person_button.clicked.connect(self._save_person)
        person_form.addRow(self.save_person_button)

        middle_panel.addWidget(person_group)

        character_group = QGroupBox("角色列表与详情")
        character_layout = QVBoxLayout(character_group)
        self.character_list = QListWidget()
        self.character_list.currentItemChanged.connect(self._on_character_selected)
        character_layout.addWidget(self.character_list)

        character_buttons = QHBoxLayout()
        self.add_character_button = QPushButton("新增角色")
        self.add_character_button.clicked.connect(self._add_character)
        self.delete_character_button = QPushButton("删除角色")
        self.delete_character_button.clicked.connect(self._delete_character)
        character_buttons.addWidget(self.add_character_button)
        character_buttons.addWidget(self.delete_character_button)
        character_layout.addLayout(character_buttons)

        character_form = QFormLayout()
        self.character_name_edit = QLineEdit()
        self.character_class_combo = QComboBox()
        for item in CharacterClass:
            self.character_class_combo.addItem(item.value, item)

        self.role_checks: dict[Role, QCheckBox] = {}
        role_layout = QHBoxLayout()
        for role in Role:
            checkbox = QCheckBox(role.value)
            self.role_checks[role] = checkbox
            role_layout.addWidget(checkbox)

        self.character_active_check = QCheckBox("启用")
        self.character_note_edit = QTextEdit()
        self.character_note_edit.setFixedHeight(80)

        character_form.addRow("角色名", self.character_name_edit)
        character_form.addRow("职业", self.character_class_combo)
        character_form.addRow("职责", self._wrap_layout(role_layout))
        character_form.addRow("状态", self.character_active_check)
        character_form.addRow("备注", self.character_note_edit)

        self.save_character_button = QPushButton("保存角色")
        self.save_character_button.clicked.connect(self._save_character)
        character_form.addRow(self.save_character_button)

        character_layout.addLayout(character_form)
        middle_panel.addWidget(character_group)

        root.addLayout(middle_panel, 3)

        self.refresh_data()

    def _wrap_layout(self, layout: QHBoxLayout) -> QWidget:
        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def refresh_data(self) -> None:
        snapshot = self.roster_service.get_snapshot()
        self.persons_by_id = {
            person.id: person for person in snapshot.persons if person.id is not None
        }
        self.characters_by_id = {}
        self.person_list.clear()

        for person in snapshot.persons:
            if person.id is None:
                continue
            item = QListWidgetItem(person.name)
            item.setData(Qt.ItemDataRole.UserRole, person.id)
            self.person_list.addItem(item)
            for character in snapshot.characters_by_person.get(person.id, []):
                if character.id is not None:
                    self.characters_by_id[character.id] = character

        if self.selected_person_id is not None:
            self._select_person_item(self.selected_person_id)

        if self.person_list.count() == 0:
            self._clear_person_form()
            self._clear_character_form()
            self.character_list.clear()

    def _select_person_item(self, person_id: int) -> None:
        for index in range(self.person_list.count()):
            item = self.person_list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == person_id:
                self.person_list.setCurrentItem(item)
                return

    def _on_person_selected(self, current: QListWidgetItem | None, _: QListWidgetItem | None) -> None:
        if current is None:
            self.selected_person_id = None
            self._clear_person_form()
            self.character_list.clear()
            self._clear_character_form()
            return

        person_id = current.data(Qt.ItemDataRole.UserRole)
        self.selected_person_id = person_id
        person = self.persons_by_id[person_id]
        self.person_name_edit.setText(person.name)
        self.person_note_edit.setPlainText(person.note)
        for day, checkbox in self.day_checks.items():
            checkbox.setChecked(day in person.default_available_days)

        self._load_characters(person_id)

    def _load_characters(self, person_id: int) -> None:
        self.character_list.clear()
        characters = self.repository.list_characters_by_person(person_id)
        self.characters_by_id = {
            character.id: character for character in characters if character.id is not None
        }
        for character in characters:
            if character.id is None:
                continue
            suffix = "启用" if character.is_active else "停用"
            item = QListWidgetItem(f"{character.name} - {character.character_class.value} - {suffix}")
            item.setData(Qt.ItemDataRole.UserRole, character.id)
            self.character_list.addItem(item)
        self.selected_character_id = None
        self._clear_character_form()

    def _on_character_selected(self, current: QListWidgetItem | None, _: QListWidgetItem | None) -> None:
        if current is None:
            self.selected_character_id = None
            self._clear_character_form()
            return

        character_id = current.data(Qt.ItemDataRole.UserRole)
        self.selected_character_id = character_id
        character = self.characters_by_id[character_id]
        self.character_name_edit.setText(character.name)
        self.character_class_combo.setCurrentIndex(
            self.character_class_combo.findText(character.character_class.value)
        )
        for role, checkbox in self.role_checks.items():
            checkbox.setChecked(role in character.roles)
        self.character_active_check.setChecked(character.is_active)
        self.character_note_edit.setPlainText(character.note)

    def _save_person(self) -> None:
        name = self.person_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "自然人昵称不能为空。")
            return
        available_days = [day for day, checkbox in self.day_checks.items() if checkbox.isChecked()]
        person = Person(
            id=self.selected_person_id,
            name=name,
            note=self.person_note_edit.toPlainText().strip(),
            default_available_days=available_days,
        )
        if self.selected_person_id is None:
            new_id = self.repository.add_person(person)
            self.selected_person_id = new_id
        else:
            self.repository.update_person(person)
        self.refresh_data()

    def _add_person(self) -> None:
        self.selected_person_id = None
        self._clear_person_form()
        self.character_list.clear()
        self._clear_character_form()
        self.person_list.clearSelection()

    def _delete_person(self) -> None:
        if self.selected_person_id is None:
            return
        result = QMessageBox.question(self, "确认", "删除自然人会同时删除其所有角色，是否继续？")
        if result != QMessageBox.StandardButton.Yes:
            return
        self.repository.delete_person(self.selected_person_id)
        self.selected_person_id = None
        self.refresh_data()

    def _save_character(self) -> None:
        if self.selected_person_id is None:
            QMessageBox.warning(self, "提示", "请先选择或保存一个自然人。")
            return
        name = self.character_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "角色名不能为空。")
            return
        roles = [role for role, checkbox in self.role_checks.items() if checkbox.isChecked()]
        if not roles:
            QMessageBox.warning(self, "提示", "至少选择一个职责。")
            return
        character = Character(
            id=self.selected_character_id,
            person_id=self.selected_person_id,
            name=name,
            character_class=self.character_class_combo.currentData(),
            roles=roles,
            is_active=self.character_active_check.isChecked(),
            note=self.character_note_edit.toPlainText().strip(),
        )
        if self.selected_character_id is None:
            new_id = self.repository.add_character(character)
            self.selected_character_id = new_id
        else:
            self.repository.update_character(character)
        self._load_characters(self.selected_person_id)

    def _add_character(self) -> None:
        if self.selected_person_id is None:
            QMessageBox.warning(self, "提示", "请先选择一个自然人。")
            return
        self.selected_character_id = None
        self._clear_character_form()
        self.character_list.clearSelection()

    def _delete_character(self) -> None:
        if self.selected_character_id is None:
            return
        result = QMessageBox.question(self, "确认", "确定删除当前角色吗？")
        if result != QMessageBox.StandardButton.Yes:
            return
        self.repository.delete_character(self.selected_character_id)
        self.selected_character_id = None
        if self.selected_person_id is not None:
            self._load_characters(self.selected_person_id)

    def _clear_person_form(self) -> None:
        self.person_name_edit.clear()
        self.person_note_edit.clear()
        for checkbox in self.day_checks.values():
            checkbox.setChecked(False)

    def _clear_character_form(self) -> None:
        self.character_name_edit.clear()
        self.character_class_combo.setCurrentIndex(0)
        for checkbox in self.role_checks.values():
            checkbox.setChecked(False)
        self.character_active_check.setChecked(True)
        self.character_note_edit.clear()
