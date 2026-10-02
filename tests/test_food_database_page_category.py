import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from nutri_app.database.schema import initialize_database
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.ui.pages.food_database_page import FoodDatabasePage


class FoodDatabasePageCategoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def _build_page(self) -> FoodDatabasePage:
        self._tmp = TemporaryDirectory()
        factory = SQLiteConnectionFactory(Path(self._tmp.name) / "test.sqlite")
        initialize_database(factory)
        return FoodDatabasePage(factory, AuditRepository(factory), current_user_id=1)

    def _fill_and_save(self, page: FoodDatabasePage, name: str, category: str) -> None:
        page.name.setText(name)
        page.category.setText(category)
        page.base_portion.setText("100")
        page.energy.setText("50")
        page._save_food()

    def _select_row_of(self, page: FoodDatabasePage, name: str) -> None:
        for row in range(page.table.rowCount()):
            if page.table.item(row, 1).text() == name:
                page._select_food_from_table(row, 0)
                return
        self.fail(f"Alimento {name} nao encontrado na tabela.")

    def test_categoria_escolhida_no_dropdown_e_gravada_e_recarregada(self) -> None:
        page = self._build_page()

        self._fill_and_save(page, "Banana teste", "Frutas")
        self._select_row_of(page, "Banana teste")

        self.assertEqual(page.category.text(), "Frutas")

    def test_categoria_antiga_fora_da_lista_nao_e_perdida_ao_editar(self) -> None:
        page = self._build_page()
        self._fill_and_save(page, "Item regional", "Regional")

        self._select_row_of(page, "Item regional")

        self.assertEqual(page.category.text(), "Regional")

    def test_nova_ficha_volta_com_categoria_vazia(self) -> None:
        page = self._build_page()
        page.category.setText("Bebidas")

        page._clear_form()

        self.assertEqual(page.category.text(), "")


if __name__ == "__main__":
    unittest.main()
