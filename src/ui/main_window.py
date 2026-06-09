from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QTabWidget

from src.app import run
from src.ui.tabs.events_tab import EventsTab
from src.ui.tabs.import_export_tab import ImportExportTab
from src.ui.tabs.roster_tab import RosterTab
from src.ui.tabs.scheduler_tab import SchedulerTab
from src.ui.tabs.settings_tab import SettingsTab
from src.ui.tabs.templates_tab import TemplatesTab


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("WOW 团队活动排班工具")
        self.resize(1280, 800)

        tabs = QTabWidget()
        tabs.addTab(RosterTab(), "自然人与角色")
        tabs.addTab(EventsTab(), "活动与班次")
        tabs.addTab(TemplatesTab(), "阵容模板")
        tabs.addTab(SchedulerTab(), "排班工作台")
        tabs.addTab(ImportExportTab(), "导入导出")
        tabs.addTab(SettingsTab(), "系统设置")
        self.setCentralWidget(tabs)


def create_application() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def launch() -> None:
    raise SystemExit(run())
