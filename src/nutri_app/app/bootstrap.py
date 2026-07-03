from __future__ import annotations

import sys

from nutri_app.app.context import build_app_context
from nutri_app.app.settings import AppSettings
from nutri_app.ui.resources.styles import load_stylesheet


def run() -> int:
    try:
        from PySide6.QtGui import QIcon
        from PySide6.QtWidgets import QApplication

        from nutri_app.ui.dialogs.login_dialog import LoginDialog
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
    if settings.icon_path.exists():
        app.setWindowIcon(QIcon(str(settings.icon_path)))

    login_dialog = LoginDialog(context.auth_service)
    if login_dialog.exec() != LoginDialog.DialogCode.Accepted or login_dialog.user is None:
        return 0

    window = MainWindow(context=context, current_user=login_dialog.user)
    window.show()
    return app.exec()
