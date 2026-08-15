import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from nutri_app.app.context import build_app_context
from nutri_app.app.settings import AppSettings
from nutri_app.domain.user import AuthenticatedUser, UserRole
from nutri_app.ui.dialogs.login_dialog import LoginDialog
from nutri_app.ui.main_window import MainWindow


class UISmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_login_e_janela_principal_sao_construidos(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            settings = AppSettings(
                app_name="Nutri Clinic Pro Test",
                organization_name="Nutri Clinic Pro",
                database_path=root / "test.sqlite",
                migrations_path=Path("database/migrations"),
                stylesheet_path=Path("src/nutri_app/ui/resources/app.qss"),
                icon_path=Path("icone.png"),
            )
            context = build_app_context(settings)
            login = LoginDialog(context.auth_service)
            window = MainWindow(
                context,
                AuthenticatedUser(1, "Admin", "admin@test.local", UserRole.ADMINISTRADOR),
            )

        self.assertEqual(login.windowTitle(), "Login")
        self.assertGreater(window.pages.count(), 20)
        window.close()
        login.close()
