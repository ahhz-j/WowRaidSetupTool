from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ImportExportTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("导入导出（开发中）"))
        layout.addWidget(QLabel("将支持名单、班次、报名及排班的文件/字符串交换。"))
