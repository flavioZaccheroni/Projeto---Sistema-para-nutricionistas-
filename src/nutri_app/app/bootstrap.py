from __future__ import annotations

import sys

from nutri_app.app.context import build_app_context
from nutri_app.app.settings import AppSettings
from nutri_app.ui.resources.styles import load_stylesheet


def run() -> int:
    try:
        from PySide6.QtWidgets import QApplication

        from nutri_app.ui.main_window import MainWindow
    except ModuleNotFoundError as exc:
        missing = exc.name or "dependencia"
        print(
            f"Dependencia ausente: {missing}. "
            "Instale as dependencias com `python -m pip install -r requirements-dev.txt`."
        )
        return 1

    settings = AppSettings.load()
    context = build_app_context(settings)
    app = QApplication(sys.argv)
    app.setApplicationName(settings.app_name)
    app.setOrganizationName(settings.organization_name)
    app.setStyleSheet(load_stylesheet(settings.stylesheet_path))

    window = MainWindow(context=context)
    window.show()
    return app.exec()
