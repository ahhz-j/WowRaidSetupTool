from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class SettingsTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("系统设置（开发中）"))
