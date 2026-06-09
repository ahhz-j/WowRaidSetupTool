"""Application entry service."""

from __future__ import annotations

from src.persistence.db import initialize_database
from src.ui.main_window import MainWindow, create_application
from src.utils.paths import ensure_directories


def run() -> int:
    ensure_directories()
    initialize_database()
    app = create_application()
    window = MainWindow()
    window.show()
    return app.exec()
