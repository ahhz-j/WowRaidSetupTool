from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class TemplatesTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("阵容模板设计（开发中）"))
