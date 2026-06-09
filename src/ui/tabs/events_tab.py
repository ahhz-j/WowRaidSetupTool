from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class EventsTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("活动与班次管理（开发中）"))
