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
from nutri_app.ui.pages.anamnesis_page import AnamnesisPage


class AnamnesisPageRepeatTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def _build_page_with_previous_anamnesis(self) -> tuple[AnamnesisPage, int]:
        self._tmp = TemporaryDirectory()
        factory = SQLiteConnectionFactory(Path(self._tmp.name) / "test.sqlite")
        initialize_database(factory)
        patient_id = PatientRepository(factory).add(
            Patient(name="Paciente Anamnese", birth_date=date(1990, 1, 1))
        )
        page = AnamnesisPage(factory, AuditRepository(factory), current_user_id=1)
        index = page.patient_ids_by_index.index(patient_id)
        page.patient.setCurrentIndex(index)
        page.chief_complaint.checkboxes["Perda de peso"].setChecked(True)
        page._save_anamnesis()
        return page, patient_id

    def test_repetir_sem_paciente_selecionado_mostra_aviso(self) -> None:
        self._tmp = TemporaryDirectory()
        factory = SQLiteConnectionFactory(Path(self._tmp.name) / "test.sqlite")
        initialize_database(factory)
        page = AnamnesisPage(factory, AuditRepository(factory), current_user_id=1)
        page.patient.setCurrentIndex(-1)

        with patch("nutri_app.ui.pages.anamnesis_page.QMessageBox.warning") as warning:
            page._repeat_last_anamnesis()

        warning.assert_called_once()

    def test_repetir_sem_anamnese_anterior_avisa_e_nao_marca_nada(self) -> None:
        self._tmp = TemporaryDirectory()
        factory = SQLiteConnectionFactory(Path(self._tmp.name) / "test.sqlite")
        initialize_database(factory)
        PatientRepository(factory).add(Patient(name="Sem Anamnese", birth_date=date(1990, 1, 1)))
        page = AnamnesisPage(factory, AuditRepository(factory), current_user_id=1)
        page.patient.setCurrentIndex(0)

        with patch("nutri_app.ui.pages.anamnesis_page.QMessageBox.information") as information:
            page._repeat_last_anamnesis()

        information.assert_called_once()
        self.assertFalse(page.chief_complaint.checkboxes["Perda de peso"].isChecked())

    def test_repetir_carrega_a_queixa_anterior_como_novo_registro(self) -> None:
        page, patient_id = self._build_page_with_previous_anamnesis()
        # _save_anamnesis ja chama _clear_form; reselecione o paciente.
        index = page.patient_ids_by_index.index(patient_id)
        page.patient.setCurrentIndex(index)

        with patch("nutri_app.ui.pages.anamnesis_page.QMessageBox.information"):
            page._repeat_last_anamnesis()

        self.assertIsNone(page.selected_anamnesis_id)
        self.assertTrue(page.chief_complaint.checkboxes["Perda de peso"].isChecked())

    def test_salvar_apos_repetir_cria_novo_registro_sem_alterar_o_original(self) -> None:
        page, patient_id = self._build_page_with_previous_anamnesis()
        index = page.patient_ids_by_index.index(patient_id)
        page.patient.setCurrentIndex(index)
        with patch("nutri_app.ui.pages.anamnesis_page.QMessageBox.information"):
            page._repeat_last_anamnesis()

        page._save_anamnesis()

        records = page.repository.list_active()
        self.assertEqual(len(records), 2)
        for record in records:
            self.assertIn("Perda de peso", record.chief_complaint)


if __name__ == "__main__":
    unittest.main()
