import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from nutri_app.database.schema import initialize_database
from nutri_app.domain.food import Food, FoodSource
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.food_repository import FoodRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.ui.pages.recipes_page import RecipesPage

RICE = Food(
    name="Arroz teste",
    source=FoodSource.CUSTOM,
    base_portion_g=100,
    energy_kcal=130,
    protein_g=2.5,
    carbohydrate_g=28,
    fat_g=0.2,
    fiber_g=1.6,
    sodium_mg=1,
)


class RecipesFoodLookupTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def _build_page(self) -> RecipesPage:
        self._tmp = TemporaryDirectory()
        factory = SQLiteConnectionFactory(Path(self._tmp.name) / "t.sqlite")
        initialize_database(factory)
        FoodRepository(factory).add(RICE)
        return RecipesPage(factory, AuditRepository(factory), current_user_id=1)

    def _type_name(self, page: RecipesPage, name: str) -> None:
        page.ingredient_name.setText(name)
        page.ingredient_name.textEdited.emit(name)

    def _add_ingredient(self, page: RecipesPage) -> None:
        # Ao adicionar, a tela recalcula a receita e avisa que falta o nome dela;
        # o aviso e modal, entao e simulado para nao travar o teste.
        with patch("nutri_app.ui.pages.recipes_page.QMessageBox.warning"):
            page._add_or_update_ingredient()

    def test_lista_de_sugestoes_vem_do_banco_de_alimentos(self) -> None:
        page = self._build_page()

        self.assertIn("Arroz teste", page.food_lookup._model.stringList())

    def test_escolher_o_alimento_preenche_unidade_quantidade_peso_e_nutrientes(self) -> None:
        page = self._build_page()

        self._type_name(page, "arroz teste")

        self.assertEqual(page.ingredient_name.text(), "Arroz teste")
        self.assertEqual(page.ingredient_unit.text(), "g")
        self.assertEqual(page.ingredient_quantity.text(), "100")
        self.assertEqual(page.ingredient_weight.text(), "100")
        self.assertEqual(page.ingredient_energy.text(), "130.0")
        self.assertEqual(page.ingredient_fiber.text(), "1.6")

    def test_alterar_a_quantidade_em_gramas_recalcula_peso_e_nutrientes(self) -> None:
        page = self._build_page()
        self._type_name(page, "Arroz teste")

        page.ingredient_quantity.setText("150")
        page.ingredient_quantity.textEdited.emit("150")

        self.assertEqual(page.ingredient_weight.text(), "150")
        self.assertEqual(page.ingredient_energy.text(), "195.0")
        self.assertEqual(page.ingredient_protein.text(), "3.8")

    def test_em_outra_unidade_o_peso_continua_manual_e_recalcula_ao_digitar(self) -> None:
        page = self._build_page()
        self._type_name(page, "Arroz teste")
        page.ingredient_unit.setText("xicara")

        page.ingredient_quantity.setText("2")
        page.ingredient_quantity.textEdited.emit("2")
        self.assertEqual(page.ingredient_weight.text(), "100")

        page.ingredient_weight.setText("200")
        page.ingredient_weight.textEdited.emit("200")
        self.assertEqual(page.ingredient_energy.text(), "260.0")

    def test_ingrediente_salvo_guarda_o_vinculo_com_o_alimento(self) -> None:
        page = self._build_page()
        self._type_name(page, "Arroz teste")

        self._add_ingredient(page)

        food_id = page.food_repository.list_active()[0].id
        self.assertEqual(len(page.ingredients), 1)
        self.assertIsNotNone(food_id)
        self.assertEqual(page.ingredients[0].food_id, food_id)

    def test_editar_ingrediente_da_tabela_restaura_o_vinculo(self) -> None:
        page = self._build_page()
        self._type_name(page, "Arroz teste")
        self._add_ingredient(page)
        self.assertIsNone(page.food_lookup.selected)

        page._select_ingredient_from_table(0, 0)

        self.assertIsNotNone(page.food_lookup.selected)
        page.ingredient_weight.setText("50")
        page.ingredient_weight.textEdited.emit("50")
        self.assertEqual(page.ingredient_energy.text(), "65.0")

    def test_nome_fora_do_banco_desvincula_e_aceita_valores_manuais(self) -> None:
        page = self._build_page()
        self._type_name(page, "Arroz teste")

        self._type_name(page, "Tempero da casa")
        page.ingredient_quantity.setText("5")
        page.ingredient_unit.setText("g")
        page.ingredient_weight.setText("5")
        page.ingredient_energy.setText("12")
        self._add_ingredient(page)

        self.assertEqual(len(page.ingredients), 1)
        self.assertIsNone(page.ingredients[0].food_id)
        self.assertEqual(page.ingredients[0].energy_kcal, 12)

    def test_limpar_o_formulario_do_ingrediente_desvincula(self) -> None:
        page = self._build_page()
        self._type_name(page, "Arroz teste")

        page._clear_ingredient_form()

        self.assertIsNone(page.food_lookup.selected)


if __name__ == "__main__":
    unittest.main()
