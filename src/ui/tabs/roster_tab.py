from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class RosterTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("自然人与角色管理（开发中）"))
