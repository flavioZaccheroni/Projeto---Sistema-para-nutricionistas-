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
from nutri_app.ui.pages.meal_plan_page import MealPlanPage


class MealPlanPageUnitTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def _build_page(self) -> MealPlanPage:
        self._tmp = TemporaryDirectory()
        factory = SQLiteConnectionFactory(Path(self._tmp.name) / "test.sqlite")
        initialize_database(factory)
        PatientRepository(factory).add(
            Patient(name="Paciente Unidade", birth_date=date(1990, 1, 1))
        )
        return MealPlanPage(factory, AuditRepository(factory), current_user_id=1)

    def test_unidade_escolhida_na_lista_chega_ao_item_do_plano(self) -> None:
        page = self._build_page()
        page.meal_name.setText("Almoco")
        page._add_meal()
        page.food.setText("Arroz")
        page.quantity.setText("2")
        page.unit.setText("colher de sopa")
        page.energy.setText("100")

        with patch("nutri_app.ui.pages.meal_plan_page_form_tab.QMessageBox.warning") as warning:
            page._add_item()

        warning.assert_not_called()
        self.assertEqual(page.meals[0].items[0].unit, "colher de sopa")

    def test_unidade_fora_da_lista_tambem_e_aceita(self) -> None:
        page = self._build_page()
        page.meal_name.setText("Lanche")
        page._add_meal()
        page.food.setText("Pao")
        page.quantity.setText("1")
        page.unit.setText("pedaco")
        page.energy.setText("80")

        with patch("nutri_app.ui.pages.meal_plan_page_form_tab.QMessageBox.warning") as warning:
            page._add_item()

        warning.assert_not_called()
        self.assertEqual(page.meals[0].items[0].unit, "pedaco")


if __name__ == "__main__":
    unittest.main()
