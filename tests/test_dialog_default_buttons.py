import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from nutri_app.app.context import build_app_context
from nutri_app.app.settings import AppSettings
from nutri_app.ui.dialogs.hospitalizations_dialog import HospitalizationsDialog
from nutri_app.ui.dialogs.login_dialog import LoginDialog, PasswordChangeDialog


class DialogDefaultButtonTest(unittest.TestCase):
    """Enter deve confirmar o dialogo pelo botao primario (QPushButton.setDefault)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def _build_context(self):
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        settings = AppSettings(
            app_name="Nutri Clinic Pro Test",
            organization_name="Nutri Clinic Pro",
            database_path=root / "test.sqlite",
            migrations_path=Path("database/migrations"),
            stylesheet_path=Path("src/nutri_app/ui/resources/app.qss"),
            icon_path=Path("icone.png"),
            seed_data_path=Path("database/seed/starter_foods.csv"),
        )
        return build_app_context(settings)

    def test_login_dialog_botao_entrar_e_padrao(self) -> None:
        context = self._build_context()
        dialog = LoginDialog(context.auth_service)
        self.assertTrue(self._find_button(dialog, "Entrar").isDefault())
        dialog.close()

    def test_password_change_dialog_botao_alterar_e_padrao(self) -> None:
        context = self._build_context()
        dialog = PasswordChangeDialog(context.auth_service, user_id=1)
        self.assertTrue(self._find_button(dialog, "Alterar senha").isDefault())
        dialog.close()

    def test_hospitalizations_dialog_botao_salvar_e_padrao(self) -> None:
        context = self._build_context()
        dialog = HospitalizationsDialog(
            context.connection_factory,
            context.audit_repository,
            current_user_id=1,
            patient_id=1,
            patient_name="Paciente Teste",
        )
        self.assertTrue(self._find_button(dialog, "Salvar internacao").isDefault())
        dialog.close()

    @staticmethod
    def _find_button(dialog, text: str):
        for button in dialog.findChildren(QPushButton):
            if button.text() == text:
                return button
        raise AssertionError(f"Botao '{text}' nao encontrado no dialogo.")


if __name__ == "__main__":
    unittest.main()
