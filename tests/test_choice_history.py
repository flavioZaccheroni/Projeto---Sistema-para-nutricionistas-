import os
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from nutri_app.database.schema import initialize_database
from nutri_app.domain.hospitalization import Hospitalization
from nutri_app.domain.laboratory_exam import LaboratoryExam
from nutri_app.domain.patient import Patient
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.choice_history_repository import ChoiceHistoryRepository
from nutri_app.repositories.hospitalization_repository import HospitalizationRepository
from nutri_app.repositories.laboratory_exam_repository import LaboratoryExamRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.ui.choice_combo import (
    INSURANCE_SEEDS,
    LAB_EXAM_NAMES,
    TextChoiceComboBox,
    merge_options,
)
from nutri_app.ui.pages.laboratory_exams_page import LaboratoryExamsPage
from nutri_app.ui.pages.patients_page import PatientsPage


class MergeOptionsTest(unittest.TestCase):
    def test_aprendidos_vem_primeiro_e_nao_repete_ignorando_caixa(self) -> None:
        merged = merge_options(["Unimed", "Bradesco"], ["particular", "unimed", "Particular"])

        self.assertEqual(merged, ["Unimed", "Bradesco", "particular"])

    def test_ignora_valores_em_branco(self) -> None:
        self.assertEqual(merge_options(["", "  ", "A"], [""]), ["A"])


class SetOptionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_set_options_mantem_o_texto_digitado(self) -> None:
        combo = TextChoiceComboBox((), editable=True)
        combo.setText("Plano novo")

        combo.set_options(["Unimed", "Bradesco"])

        self.assertEqual(combo.text(), "Plano novo")
        self.assertEqual(combo.count(), 2)

    def test_set_options_seleciona_item_igual_ao_texto_atual(self) -> None:
        combo = TextChoiceComboBox((), editable=True)
        combo.setText("unimed")

        combo.set_options(["Unimed"])

        self.assertEqual(combo.text(), "Unimed")

    def test_placeholder_e_tamanho_maximo_vao_para_o_campo_de_edicao(self) -> None:
        combo = TextChoiceComboBox((), editable=True)

        combo.setPlaceholderText("Convenio")
        combo.setMaxLength(5)

        self.assertEqual(combo.lineEdit().placeholderText(), "Convenio")
        self.assertEqual(combo.lineEdit().maxLength(), 5)


class ChoiceHistoryRepositoryTest(unittest.TestCase):
    def _factory(self) -> tuple[SQLiteConnectionFactory, TemporaryDirectory]:
        tmp = TemporaryDirectory()
        factory = SQLiteConnectionFactory(Path(tmp.name) / "test.sqlite")
        initialize_database(factory)
        return factory, tmp

    def _add_patient(self, factory, name: str, insurance: str) -> int:
        return PatientRepository(factory).add(
            Patient(name=name, birth_date=date(1990, 1, 1), health_insurance=insurance)
        )

    def test_ordena_por_uso_e_junta_grafias_diferentes(self) -> None:
        factory, tmp = self._factory()
        with tmp:
            self._add_patient(factory, "A", "Unimed")
            self._add_patient(factory, "B", "unimed")
            self._add_patient(factory, "C", "Unimed")
            self._add_patient(factory, "D", "Bradesco")

            values = ChoiceHistoryRepository(factory).values("patient_insurance")

        self.assertEqual(values, ["Unimed", "Bradesco"])

    def test_ignora_vazios_e_pacientes_excluidos(self) -> None:
        factory, tmp = self._factory()
        with tmp:
            self._add_patient(factory, "A", "")
            removed = self._add_patient(factory, "B", "SulAmerica")
            PatientRepository(factory).soft_delete(removed)
            self._add_patient(factory, "C", "Amil")

            values = ChoiceHistoryRepository(factory).values("patient_insurance")

        self.assertEqual(values, ["Amil"])

    def test_convenio_tambem_aprende_com_internacoes(self) -> None:
        factory, tmp = self._factory()
        with tmp:
            patient_id = self._add_patient(factory, "A", "")
            HospitalizationRepository(factory).add(
                Hospitalization(
                    patient_id=patient_id,
                    admission_date=date(2026, 1, 1),
                    unit="UTI",
                    health_insurance="Porto Seguro",
                )
            )

            values = ChoiceHistoryRepository(factory).values("patient_insurance")

        self.assertEqual(values, ["Porto Seguro"])


class ScreensLearnOptionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def _items(self, combo: TextChoiceComboBox) -> list[str]:
        return [combo.itemText(index) for index in range(combo.count())]

    def test_pacientes_oferece_convenios_ja_cadastrados_e_particular(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            PatientRepository(factory).add(
                Patient(name="A", birth_date=date(1990, 1, 1), health_insurance="Unimed")
            )

            page = PatientsPage(factory, AuditRepository(factory), current_user_id=1)

            self.assertEqual(self._items(page.health_insurance), ["Unimed", *INSURANCE_SEEDS])

    def test_exames_oferece_nomes_comuns_e_laboratorios_ja_usados(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            patient_id = PatientRepository(factory).add(
                Patient(name="A", birth_date=date(1990, 1, 1))
            )
            LaboratoryExamRepository(factory).add(
                LaboratoryExam(
                    patient_id=patient_id, exam_date=date(2026, 1, 1), laboratory="Fleury"
                )
            )

            page = LaboratoryExamsPage(factory, AuditRepository(factory), current_user_id=1)

            self.assertEqual(self._items(page.laboratory), ["Fleury"])
            self.assertEqual(self._items(page.item_name), list(LAB_EXAM_NAMES))
            self.assertIn("mg/dL", self._items(page.item_unit))

    def test_valor_digitado_livremente_continua_valido_em_exames(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            page = LaboratoryExamsPage(factory, AuditRepository(factory), current_user_id=1)

            page.item_name.setText("Exame muito raro")

            self.assertEqual(page.item_name.text(), "Exame muito raro")


if __name__ == "__main__":
    unittest.main()
