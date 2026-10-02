import os
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from nutri_app.database.schema import initialize_database
from nutri_app.domain.patient import Patient
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.ui.pages.patient_app_page import PatientAppPage


class PatientAppEmailPrefillTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def _setup(self):
        self._tmp = TemporaryDirectory()
        factory = SQLiteConnectionFactory(Path(self._tmp.name) / "t.sqlite")
        initialize_database(factory)
        patients = PatientRepository(factory)
        ids = {
            name: patients.add(Patient(name=name, birth_date=date(1990, 1, 1), email=email))
            for name, email in [
                ("Ana", "ana@exemplo.com"),
                ("Bruno", ""),
                ("Carla", "carla@exemplo.com"),
            ]
        }
        page = PatientAppPage(factory, AuditRepository(factory), current_user_id=1)
        return page, ids

    def _select(self, page: PatientAppPage, patient_id: int) -> None:
        page.patient.setCurrentIndex(page.patient_ids_by_index.index(patient_id))

    def test_traz_o_email_do_cadastro_do_paciente(self) -> None:
        page, ids = self._setup()

        self._select(page, ids["Carla"])

        self.assertEqual(page.email.text(), "carla@exemplo.com")

    def test_troca_o_email_ao_trocar_de_paciente_e_limpa_se_nao_houver(self) -> None:
        page, ids = self._setup()
        self._select(page, ids["Carla"])

        self._select(page, ids["Bruno"])
        self.assertEqual(page.email.text(), "")

        self._select(page, ids["Ana"])
        self.assertEqual(page.email.text(), "ana@exemplo.com")

    def test_nao_sobrescreve_o_email_digitado(self) -> None:
        page, ids = self._setup()
        self._select(page, ids["Ana"])
        page.email.setText("outro@exemplo.com")

        self._select(page, ids["Carla"])

        self.assertEqual(page.email.text(), "outro@exemplo.com")


if __name__ == "__main__":
    unittest.main()
