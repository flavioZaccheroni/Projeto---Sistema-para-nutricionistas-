import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from nutri_app.database.schema import initialize_database
from nutri_app.domain.user import User, UserRole
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.repositories.user_repository import UserRepository
from nutri_app.ui.pages.reports_page import ReportsPage


class ReportsPagePrefillTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def _build_page(self, professional_registration: str | None) -> ReportsPage:
        self._tmp = TemporaryDirectory()
        factory = SQLiteConnectionFactory(Path(self._tmp.name) / "test.sqlite")
        initialize_database(factory)
        user_repository = UserRepository(factory)
        user_id = user_repository.add(
            User(
                name="Dra. Ana Nutri",
                email="ana@nutri.com",
                password_hash="hash",
                role=UserRole.NUTRICIONISTA,
                professional_registration=professional_registration,
            )
        )
        return ReportsPage(factory, AuditRepository(factory), user_id)

    def test_preenche_profissional_e_crn_do_usuario_logado(self) -> None:
        page = self._build_page("CRN-3 12345")

        self.assertEqual(page.professional_name.text(), "Dra. Ana Nutri")
        self.assertEqual(page.professional_registration.text(), "CRN-3 12345")

    def test_limpar_formulario_nao_apaga_profissional_e_crn(self) -> None:
        page = self._build_page("CRN-3 12345")

        page._clear_form()

        self.assertEqual(page.professional_name.text(), "Dra. Ana Nutri")
        self.assertEqual(page.professional_registration.text(), "CRN-3 12345")

    def test_funciona_sem_crn_cadastrado(self) -> None:
        page = self._build_page(None)

        self.assertEqual(page.professional_name.text(), "Dra. Ana Nutri")
        self.assertEqual(page.professional_registration.text(), "")


if __name__ == "__main__":
    unittest.main()
