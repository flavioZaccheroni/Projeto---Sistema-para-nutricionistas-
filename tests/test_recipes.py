import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.schema import initialize_database
from nutri_app.domain.recipe import Recipe, RecipeIngredient
from nutri_app.repositories.recipe_repository import RecipeRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.recipe import RecipeService


class RecipeServiceTest(unittest.TestCase):
    def test_calcula_totais_por_porcao_e_por_100g(self) -> None:
        service = RecipeService()
        ingredients = [
            RecipeIngredient(
                name="Aveia",
                quantity=100,
                unit="g",
                weight_g=100,
                energy_kcal=380,
                protein_g=13,
                carbohydrate_g=67,
                fat_g=7,
                fiber_g=10,
                sodium_mg=5,
            ),
            RecipeIngredient(
                name="Banana",
                quantity=200,
                unit="g",
                weight_g=200,
                energy_kcal=180,
                protein_g=2,
                carbohydrate_g=46,
                fat_g=0.6,
                fiber_g=5,
                sodium_mg=2,
            ),
        ]
        totals = service.calculate_totals(ingredients)
        recipe = Recipe(
            name="Bolo simples",
            servings=4,
            total_weight_g=400,
            total_energy_kcal=totals.energy_kcal,
            total_protein_g=totals.protein_g,
            total_carbohydrate_g=totals.carbohydrate_g,
            total_fat_g=totals.fat_g,
            total_fiber_g=totals.fiber_g,
            total_sodium_mg=totals.sodium_mg,
            ingredients=ingredients,
        )

        serving = service.calculate_per_serving(recipe)
        per_100g = service.calculate_per_100g(recipe)

        self.assertAlmostEqual(totals.energy_kcal, 560)
        self.assertAlmostEqual(serving.energy_kcal, 140)
        self.assertAlmostEqual(per_100g.energy_kcal, 140)
        self.assertAlmostEqual(serving.protein_g, 3.75)

    def test_rejeita_receita_sem_ingredientes(self) -> None:
        with self.assertRaises(ValueError):
            RecipeService().validate_recipe(
                Recipe(name="Receita vazia", servings=1, total_weight_g=100)
            )


class RecipeRepositoryTest(unittest.TestCase):
    def test_cria_lista_atualiza_e_exclui_receita(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            repository = RecipeRepository(factory)

            recipe_id = repository.add(
                Recipe(
                    name="Panqueca",
                    category="Cafe da manha",
                    servings=2,
                    total_weight_g=250,
                    preparation_method="Misturar e grelhar.",
                    total_energy_kcal=420,
                    total_protein_g=22,
                    total_carbohydrate_g=48,
                    total_fat_g=14,
                    total_fiber_g=5,
                    total_sodium_mg=180,
                    ingredients=[
                        RecipeIngredient(
                            name="Ovo",
                            quantity=2,
                            unit="un",
                            weight_g=100,
                            energy_kcal=140,
                            protein_g=12,
                            carbohydrate_g=1,
                            fat_g=10,
                        ),
                        RecipeIngredient(
                            name="Aveia",
                            quantity=80,
                            unit="g",
                            weight_g=80,
                            energy_kcal=280,
                            protein_g=10,
                            carbohydrate_g=47,
                            fat_g=4,
                            fiber_g=5,
                            sodium_mg=180,
                        ),
                    ],
                )
            )
            listed = repository.list_active("panqueca")
            loaded = repository.get(recipe_id)
            repository.update(
                Recipe(
                    id=recipe_id,
                    name="Panqueca proteica",
                    category="Lanche",
                    servings=2,
                    total_weight_g=260,
                    preparation_method="Misturar, grelhar e servir.",
                    total_energy_kcal=450,
                    total_protein_g=30,
                    total_carbohydrate_g=45,
                    total_fat_g=15,
                    total_fiber_g=6,
                    total_sodium_mg=190,
                    notes="Atualizada",
                    ingredients=[
                        RecipeIngredient(
                            name="Ovo",
                            quantity=2,
                            unit="un",
                            weight_g=100,
                            energy_kcal=140,
                            protein_g=12,
                            carbohydrate_g=1,
                            fat_g=10,
                        )
                    ],
                )
            )
            updated = repository.get(recipe_id)
            repository.soft_delete(recipe_id)
            after_delete = repository.list_active()

        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].name, "Panqueca")
        self.assertEqual(len(loaded.ingredients), 2)
        self.assertEqual(updated.name, "Panqueca proteica")
        self.assertEqual(len(updated.ingredients), 1)
        self.assertEqual(updated.notes, "Atualizada")
        self.assertEqual(after_delete, [])


if __name__ == "__main__":
    unittest.main()
