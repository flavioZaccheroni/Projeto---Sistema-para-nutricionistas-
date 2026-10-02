import os
import unittest
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from nutri_app.database.schema import initialize_database
from nutri_app.domain.anthropometry import Anthropometry
from nutri_app.domain.patient import Patient
from nutri_app.repositories.anthropometry_repository import AnthropometryRepository
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.ui.pages.anthropometry_page import AnthropometryPage


class AnthropometryAdvancedPrefillTest(unittest.TestCase):
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
        AnthropometryRepository(factory).add(
            Anthropometry(
                patient_id=ana,
                assessment_date=date.today() - timedelta(days=2),
                weight_kg=64.5,
                height_m=1.68,
                bmi=22.9,
                bmi_classification="Eutrofia",
                waist_cm=76,
                hip_cm=98,
            )
        )
        page = AnthropometryPage(factory, AuditRepository(factory), current_user_id=1)
        return page, ana, bruno

    def _select(self, page: AnthropometryPage, patient_id: int) -> None:
        index = page.advanced_patient_ids_by_index.index(patient_id)
        page.advanced_patient.setCurrentIndex(index)

    def test_aba_avancada_traz_as_medidas_da_ultima_antropometria(self) -> None:
        page, ana, bruno = self._setup()
        self._select(page, bruno)

        self._select(page, ana)

        inputs = page.advanced_inputs
        self.assertEqual(inputs["weight"].text(), "64.5")
        self.assertEqual(inputs["height_cm"].text(), "168")
        self.assertEqual(inputs["waist"].text(), "76")
        self.assertEqual(inputs["hip"].text(), "98")
        self.assertNotEqual(page.advanced_bmi.text(), "")

    def test_trocar_para_paciente_sem_medidas_limpa_o_que_era_automatico(self) -> None:
        page, ana, bruno = self._setup()
        self._select(page, ana)

        self._select(page, bruno)

        self.assertEqual(page.advanced_inputs["weight"].text(), "")
        self.assertEqual(page.advanced_inputs["waist"].text(), "")

    def test_nao_sobrescreve_valor_digitado(self) -> None:
        page, ana, bruno = self._setup()
        self._select(page, bruno)
        page.advanced_inputs["weight"].setText("90")

        self._select(page, ana)

        self.assertEqual(page.advanced_inputs["weight"].text(), "90")
        self.assertEqual(page.advanced_inputs["height_cm"].text(), "168")


if __name__ == "__main__":
    unittest.main()
