import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.schema import initialize_database
from nutri_app.domain.food import Food, FoodSource
from nutri_app.repositories.food_repository import FoodRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.food import FoodService


class FoodServiceTest(unittest.TestCase):
    def test_calcula_nutrientes_por_porcao(self) -> None:
        food = Food(
            name="Arroz cozido",
            source=FoodSource.TACO,
            base_portion_g=100,
            energy_kcal=128,
            protein_g=2.5,
            carbohydrate_g=28.1,
            fat_g=0.2,
            fiber_g=1.6,
            sodium_mg=1,
        )

        nutrients = FoodService().calculate_portion(food, 50)

        self.assertAlmostEqual(nutrients.energy_kcal, 64)
        self.assertAlmostEqual(nutrients.protein_g, 1.25)
        self.assertAlmostEqual(nutrients.carbohydrate_g, 14.05)

    def test_rejeita_alimento_sem_nome(self) -> None:
        with self.assertRaises(ValueError):
            FoodService().validate(Food(name="", source=FoodSource.CUSTOM))


class FoodRepositoryTest(unittest.TestCase):
    def test_cria_lista_atualiza_e_exclui_alimento(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            repository = FoodRepository(factory)

            food_id = repository.add(
                Food(
                    name="Feijao carioca",
                    category="Leguminosas",
                    source=FoodSource.TBCA,
                    base_portion_g=100,
                    household_measure="1 concha media",
                    energy_kcal=76,
                    protein_g=4.8,
                    carbohydrate_g=13.6,
                    fat_g=0.5,
                    fiber_g=8.5,
                    sodium_mg=2,
                    glycemic_index=24,
                    micronutrients="Ferro, potassio",
                    notes="Cozido",
                )
            )
            listed = repository.list_active("feijao")
            repository.update(
                Food(
                    id=food_id,
                    name="Feijao carioca cozido",
                    category="Leguminosas",
                    source=FoodSource.REGIONAL,
                    base_portion_g=100,
                    household_measure="1 concha",
                    energy_kcal=80,
                    protein_g=5,
                    carbohydrate_g=14,
                    fat_g=0.6,
                    fiber_g=8,
                    sodium_mg=3,
                    glycemic_index=25,
                    micronutrients="Ferro",
                    notes="Atualizado",
                )
            )
            updated = repository.get(food_id)
            repository.soft_delete(food_id)
            after_delete = repository.list_active()

        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].name, "Feijao carioca")
        self.assertEqual(updated.name, "Feijao carioca cozido")
        self.assertEqual(updated.source, FoodSource.REGIONAL)
        self.assertEqual(updated.notes, "Atualizado")
        self.assertEqual(after_delete, [])


if __name__ == "__main__":
    unittest.main()
