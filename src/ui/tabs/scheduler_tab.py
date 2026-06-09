from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class SchedulerTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("排班工作台（开发中）"))
        layout.addWidget(QLabel("后续将在此提供自动排班、手工修正以及 Buff/Debuff 覆盖检查。"))
