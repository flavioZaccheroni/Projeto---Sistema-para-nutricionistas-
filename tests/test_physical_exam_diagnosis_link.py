import os
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from nutri_app.database.schema import initialize_database
from nutri_app.domain.nutrition_diagnosis import (
    DiagnosisProtocol,
    DiagnosisSeverity,
    NutritionDiagnosis,
)
from nutri_app.domain.patient import Patient
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.nutrition_diagnosis_repository import NutritionDiagnosisRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.ui.pages.physical_exam_page import NO_DIAGNOSIS, PhysicalExamPage


class PhysicalExamDiagnosisLinkTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def _setup(self):
        self._tmp = TemporaryDirectory()
        factory = SQLiteConnectionFactory(Path(self._tmp.name) / "t.sqlite")
        initialize_database(factory)
        patients = PatientRepository(factory)
        ana = patients.add(Patient(name="Ana", birth_date=date(1990, 1, 1)))
        bruno = patients.add(Patient(name="Bruno", birth_date=date(1985, 1, 1)))
        diagnosis_id = NutritionDiagnosisRepository(factory).add(
            NutritionDiagnosis(
                patient_id=ana,
                diagnosis_date=date(2026, 9, 1),
                protocol=DiagnosisProtocol.GLIM,
                criteria="criterios",
                classification="desnutricao",
                severity=DiagnosisSeverity.MODERATE,
            )
        )
        page = PhysicalExamPage(factory, AuditRepository(factory), current_user_id=1)
        return page, factory, ana, bruno, diagnosis_id

    def _select(self, page: PhysicalExamPage, patient_id: int) -> None:
        page.patient.setCurrentIndex(page.patient_ids.index(patient_id))

    def _items(self, page: PhysicalExamPage) -> list[str]:
        return [page.diagnosis.itemText(i) for i in range(page.diagnosis.count())]

    def test_lista_apenas_os_diagnosticos_do_paciente_selecionado(self) -> None:
        page, _factory, ana, bruno, _diagnosis_id = self._setup()

        self._select(page, ana)
        self.assertEqual(len(self._items(page)), 2)
        self.assertIn("GLIM: desnutricao (moderada)", self._items(page)[1])
        self.assertIn("01/09/2026", self._items(page)[1])

        self._select(page, bruno)
        self.assertEqual(self._items(page), [NO_DIAGNOSIS])

    def test_salvar_com_diagnostico_escolhido_grava_o_vinculo(self) -> None:
        page, factory, ana, _bruno, diagnosis_id = self._setup()
        self._select(page, ana)
        page.diagnosis.setCurrentIndex(1)
        page.summary.setPlainText("Resumo dos achados")

        with (
            patch("nutri_app.ui.pages.physical_exam_page.QMessageBox.warning") as warning,
            patch("nutri_app.ui.pages.physical_exam_page.QMessageBox.information"),
        ):
            page._save()

        warning.assert_not_called()
        saved = page.repository.list_for_patient(ana)
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0].diagnosis_id, diagnosis_id)

    def test_salvar_sem_escolher_deixa_o_vinculo_vazio(self) -> None:
        page, _factory, ana, _bruno, _diagnosis_id = self._setup()
        self._select(page, ana)
        page.summary.setPlainText("Resumo")

        with (
            patch("nutri_app.ui.pages.physical_exam_page.QMessageBox.warning"),
            patch("nutri_app.ui.pages.physical_exam_page.QMessageBox.information"),
        ):
            page._save()

        self.assertIsNone(page.repository.list_for_patient(ana)[0].diagnosis_id)

    def test_refresh_mostra_paciente_cadastrado_depois_e_mantem_a_selecao(self) -> None:
        page, factory, ana, _bruno, _diagnosis_id = self._setup()
        self._select(page, ana)
        novo = PatientRepository(factory).add(Patient(name="Carla", birth_date=date(1995, 1, 1)))
        self.assertNotIn(novo, page.patient_ids)

        page.refresh()

        self.assertIn(novo, page.patient_ids)
        self.assertEqual(page.patient_ids[page.patient.currentIndex()], ana)


if __name__ == "__main__":
    unittest.main()
