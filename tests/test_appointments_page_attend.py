import os
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from nutri_app.database.schema import initialize_database
from nutri_app.domain.patient import Patient
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.ui.pages.appointments_page import AppointmentsPage


class AppointmentsPageAttendTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def _build_page(self) -> tuple[AppointmentsPage, int]:
        self._tmp = TemporaryDirectory()
        factory = SQLiteConnectionFactory(Path(self._tmp.name) / "test.sqlite")
        initialize_database(factory)
        patient_id = PatientRepository(factory).add(
            Patient(name="Paciente Atender", birth_date=date(1990, 1, 1))
        )
        page = AppointmentsPage(factory, AuditRepository(factory), current_user_id=1)
        return page, patient_id

    def test_atender_emite_o_id_do_paciente_selecionado(self) -> None:
        page, patient_id = self._build_page()
        index = page.patient_ids_by_index.index(patient_id)
        page.patient.setCurrentIndex(index)

        received: list[int] = []
        page.attend_requested.connect(received.append)

        page._request_attend()

        self.assertEqual(received, [patient_id])

    def test_atender_sem_paciente_nao_emite_sinal(self) -> None:
        self._tmp = TemporaryDirectory()
        factory = SQLiteConnectionFactory(Path(self._tmp.name) / "test.sqlite")
        initialize_database(factory)
        page = AppointmentsPage(factory, AuditRepository(factory), current_user_id=1)

        received: list[int] = []
        page.attend_requested.connect(received.append)

        with patch("nutri_app.ui.pages.appointments_page.QMessageBox.warning") as warning:
            page._request_attend()

        warning.assert_called_once()
        self.assertEqual(received, [])


if __name__ == "__main__":
    unittest.main()
