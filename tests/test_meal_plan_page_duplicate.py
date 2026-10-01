import os
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from nutri_app.database.schema import initialize_database
from nutri_app.domain.meal_plan import Meal, MealPlan, MealPlanItem
from nutri_app.domain.patient import Patient
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.meal_plan_repository import MealPlanRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.ui.pages.meal_plan_page import MealPlanPage


class MealPlanPageDuplicateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def _build_page(self) -> tuple[MealPlanPage, int]:
        self._tmp = TemporaryDirectory()
        factory = SQLiteConnectionFactory(Path(self._tmp.name) / "test.sqlite")
        initialize_database(factory)
        patient_id = PatientRepository(factory).add(
            Patient(name="Paciente Plano", birth_date=date(1990, 1, 1))
        )
        MealPlanRepository(factory).add(
            MealPlan(
                patient_id=patient_id,
                start_date=date(2026, 1, 10),
                objective="Emagrecimento",
                target_energy_kcal=1800,
                notes="Plano antigo",
                meals=[
                    Meal(
                        name="Almoco",
                        time="12:00",
                        items=[
                            MealPlanItem(
                                food="Arroz branco cozido", quantity=120, unit="g", energy_kcal=150
                            )
                        ],
                    )
                ],
            )
        )
        page = MealPlanPage(factory, AuditRepository(factory), current_user_id=1)
        return page, patient_id

    def test_duplicar_sem_paciente_selecionado_mostra_aviso(self) -> None:
        page, _patient_id = self._build_page()
        page.patient.setCurrentIndex(-1)

        with patch(
            "nutri_app.ui.pages.meal_plan_page_form_tab.QMessageBox.warning"
        ) as warning:
            page._duplicate_last_plan()

        warning.assert_called_once()

    def test_duplicar_sem_plano_anterior_avisa_e_nao_altera_formulario(self) -> None:
        self._tmp = TemporaryDirectory()
        factory = SQLiteConnectionFactory(Path(self._tmp.name) / "test.sqlite")
        initialize_database(factory)
        PatientRepository(factory).add(Patient(name="Sem Plano", birth_date=date(1990, 1, 1)))
        page = MealPlanPage(factory, AuditRepository(factory), current_user_id=1)
        page.patient.setCurrentIndex(0)

        with patch(
            "nutri_app.ui.pages.meal_plan_page_form_tab.QMessageBox.information"
        ) as information:
            page._duplicate_last_plan()

        information.assert_called_once()
        self.assertEqual(page.meals, [])

    def test_duplicar_carrega_o_ultimo_plano_como_novo_registro(self) -> None:
        page, patient_id = self._build_page()
        index = page.patient_ids_by_index.index(patient_id)
        page.patient.setCurrentIndex(index)

        with patch("nutri_app.ui.pages.meal_plan_page_form_tab.QMessageBox.information"):
            page._duplicate_last_plan()

        self.assertIsNone(page.selected_plan_id)
        self.assertEqual(page.objective.text(), "Emagrecimento")
        self.assertEqual(page.target_energy.text(), "1800")
        self.assertEqual(len(page.meals), 1)
        self.assertEqual(page.meals[0].name, "Almoco")
        self.assertEqual(page.meals[0].items[0].food, "Arroz branco cozido")

    def test_salvar_apos_duplicar_cria_um_novo_plano_sem_alterar_o_original(self) -> None:
        page, patient_id = self._build_page()
        index = page.patient_ids_by_index.index(patient_id)
        page.patient.setCurrentIndex(index)

        with patch("nutri_app.ui.pages.meal_plan_page_form_tab.QMessageBox.information"):
            page._duplicate_last_plan()
        page._save_plan()

        all_plans = page.repository.list_active()
        self.assertEqual(len(all_plans), 2)
        objectives = sorted(plan.objective for plan in all_plans)
        self.assertEqual(objectives, ["Emagrecimento", "Emagrecimento"])


if __name__ == "__main__":
    unittest.main()
