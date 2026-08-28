import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.schema import initialize_database
from nutri_app.domain.food import Food, FoodSource
from nutri_app.repositories.food_repository import FoodRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.food_seed import seed_starter_foods

STARTER_CSV = Path(__file__).resolve().parents[1] / "database" / "seed" / "starter_foods.csv"


class FoodSeedTest(unittest.TestCase):
    def test_popula_banco_vazio_com_alimentos_iniciais(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)

            inserted = seed_starter_foods(factory, STARTER_CSV)
            foods = FoodRepository(factory).list_active()

        self.assertGreater(inserted, 50)
        self.assertEqual(len(foods), inserted)
        self.assertTrue(any(food.name == "Arroz branco cozido" for food in foods))
        self.assertTrue(all(food.source == FoodSource.REGIONAL for food in foods))

    def test_nao_duplica_quando_banco_ja_possui_alimentos(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            FoodRepository(factory).add(
                Food(name="Alimento existente", source=FoodSource.CUSTOM)
            )

            inserted = seed_starter_foods(factory, STARTER_CSV)
            foods = FoodRepository(factory).list_active()

        self.assertEqual(inserted, 0)
        self.assertEqual(len(foods), 1)

    def test_nao_falha_quando_arquivo_de_seed_nao_existe(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)

            inserted = seed_starter_foods(factory, Path(tmp) / "nao_existe.csv")

        self.assertEqual(inserted, 0)


if __name__ == "__main__":
    unittest.main()
