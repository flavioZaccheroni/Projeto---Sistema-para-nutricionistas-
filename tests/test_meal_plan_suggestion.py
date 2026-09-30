import unittest

from nutri_app.domain.food import Food, FoodGroup, FoodSource
from nutri_app.services.meal_plan_suggestion import MealPlanSuggestionService


def _food(name: str, group: FoodGroup, energy_kcal: float, sodium_mg: float = 1, **kwargs) -> Food:
    return Food(
        name=name,
        source=FoodSource.REGIONAL,
        category=group.value,
        base_portion_g=100,
        energy_kcal=energy_kcal,
        protein_g=kwargs.get("protein_g", 5),
        carbohydrate_g=kwargs.get("carbohydrate_g", 10),
        fat_g=kwargs.get("fat_g", 2),
        sodium_mg=sodium_mg,
        glycemic_index=kwargs.get("glycemic_index"),
        id=kwargs.get("id", 1),
    )


def _standard_foods() -> list[Food]:
    return [
        _food("Arroz branco", FoodGroup.CEREAIS_TUBERCULOS, 128, id=1),
        _food("Batata doce", FoodGroup.CEREAIS_TUBERCULOS, 77, id=2),
        _food("Feijao carioca", FoodGroup.LEGUMINOSAS, 76, id=3),
        _food("Frango grelhado", FoodGroup.CARNES_OVOS, 159, id=4),
        _food("Peixe grelhado", FoodGroup.CARNES_OVOS, 96, id=5),
        _food("Brocolis", FoodGroup.HORTALICAS, 25, id=6),
        _food("Banana", FoodGroup.FRUTAS, 79, id=7),
        _food("Iogurte natural", FoodGroup.LATICINIOS, 105, id=8),
        _food("Azeite de oliva", FoodGroup.GORDURAS_OLEOS, 88, id=9),
        _food("Acucar refinado", FoodGroup.ACUCARES_DOCES, 39, id=10),
    ]


class MealPlanSuggestionServiceTest(unittest.TestCase):
    def test_gera_seis_refeicoes_com_itens_ligados_ao_banco(self) -> None:
        result = MealPlanSuggestionService().suggest(
            "Emagrecimento", 2000, 6, [], _standard_foods()
        )

        self.assertEqual(len(result.meals), 6)
        self.assertEqual(result.meals[0].name, "Cafe da manha")
        total_items = sum(len(meal.items) for meal in result.meals)
        self.assertGreater(total_items, 0)
        for meal in result.meals:
            for item in meal.items:
                self.assertIsNotNone(item.food_id)
                self.assertGreater(item.energy_kcal, 0)

    def test_perfil_diabetes_exclui_grupo_acucares_e_doces(self) -> None:
        result = MealPlanSuggestionService().suggest(
            "Diabetes", 2000, 6, [], _standard_foods()
        )

        chosen_names = {item.food for meal in result.meals for item in meal.items}
        self.assertNotIn("Acucar refinado", chosen_names)

    def test_perfil_dash_exclui_alimento_de_sodio_alto(self) -> None:
        foods = _standard_foods() + [
            _food("Azeitona em conserva", FoodGroup.HORTALICAS, 20, sodium_mg=800, id=11)
        ]

        result = MealPlanSuggestionService().suggest("DASH", 2000, 6, [], foods)

        chosen_names = {item.food for meal in result.meals for item in meal.items}
        self.assertNotIn("Azeitona em conserva", chosen_names)

    def test_termos_restritos_excluem_alimento(self) -> None:
        result = MealPlanSuggestionService().suggest(
            "Emagrecimento", 2000, 6, ["frango"], _standard_foods()
        )

        chosen_names = {item.food for meal in result.meals for item in meal.items}
        self.assertNotIn("Frango grelhado", chosen_names)
        self.assertIn("Peixe grelhado", chosen_names)

    def test_gera_notas_de_substituicao(self) -> None:
        result = MealPlanSuggestionService().suggest(
            "Emagrecimento", 2000, 6, [], _standard_foods()
        )

        self.assertTrue(any("Cereais e tuberculos" in note for note in result.substitution_notes))

    def test_perfil_hemodialise_gera_aviso_de_cautela(self) -> None:
        result = MealPlanSuggestionService().suggest(
            "Hemodialise", 2000, 6, [], _standard_foods()
        )

        self.assertIn("potassio", result.caution_note)

    def test_quantidade_refeicoes_diferente_de_seis_usa_template_generico(self) -> None:
        result = MealPlanSuggestionService().suggest(
            "Emagrecimento", 1800, 3, [], _standard_foods()
        )

        self.assertEqual(len(result.meals), 3)
        self.assertEqual(result.meals[0].name, "Refeicao 1")

    def test_rejeita_meta_energia_invalida(self) -> None:
        with self.assertRaises(ValueError):
            MealPlanSuggestionService().suggest("Emagrecimento", 0, 6, [], _standard_foods())

    def test_rejeita_quando_banco_de_alimentos_esta_vazio(self) -> None:
        with self.assertRaises(ValueError):
            MealPlanSuggestionService().suggest("Emagrecimento", 2000, 6, [], [])


if __name__ == "__main__":
    unittest.main()
