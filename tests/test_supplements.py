import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.schema import initialize_database
from nutri_app.domain.supplement import Supplement, SupplementType
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.repositories.supplement_repository import SupplementRepository
from nutri_app.services.supplement import SupplementService


class SupplementServiceTest(unittest.TestCase):
    def test_calcula_dose_proporcional(self) -> None:
        supplement = Supplement(
            name="Formula 1.5",
            supplement_type=SupplementType.ENTERAL_FORMULA,
            base_portion=100,
            energy_kcal=150,
            protein_g=6,
            carbohydrate_g=18,
            fat_g=5,
            fiber_g=2,
            sodium_mg=90,
        )

        result = SupplementService().calculate_dose(supplement, 200)

        self.assertAlmostEqual(result.energy_kcal, 300)
        self.assertAlmostEqual(result.protein_g, 12)
        self.assertAlmostEqual(result.sodium_mg, 180)

    def test_rejeita_suplemento_sem_nome(self) -> None:
        with self.assertRaises(ValueError):
            SupplementService().validate(
                Supplement(name="", supplement_type=SupplementType.OTHER)
            )


class SupplementRepositoryTest(unittest.TestCase):
    def test_cria_lista_atualiza_e_exclui_suplemento(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            repository = SupplementRepository(factory)

            supplement_id = repository.add(
                Supplement(
                    name="Modulo proteico",
                    supplement_type=SupplementType.PROTEIN_MODULE,
                    manufacturer="Nutri Lab",
                    presentation="Lata 400g",
                    base_portion=30,
                    portion_unit="g",
                    caloric_density=3.8,
                    osmolarity=350,
                    energy_kcal=114,
                    protein_g=24,
                    carbohydrate_g=2,
                    fat_g=1,
                    composition="Proteina isolada",
                    indications="Aporte proteico",
                    contraindications="Alergia a proteina do leite",
                    notes="Uso supervisionado",
                )
            )
            listed = repository.list_active("proteico")
            repository.update(
                Supplement(
                    id=supplement_id,
                    name="Modulo proteico atualizado",
                    supplement_type=SupplementType.PROTEIN_MODULE,
                    manufacturer="Nutri Lab",
                    presentation="Lata 400g",
                    base_portion=30,
                    portion_unit="g",
                    caloric_density=4,
                    osmolarity=360,
                    energy_kcal=120,
                    protein_g=25,
                    carbohydrate_g=2,
                    fat_g=1,
                    composition="Proteina isolada",
                    indications="Aporte proteico aumentado",
                    contraindications="Alergia",
                    notes="Atualizado",
                )
            )
            updated = repository.get(supplement_id)
            repository.soft_delete(supplement_id)
            after_delete = repository.list_active()

        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].name, "Modulo proteico")
        self.assertEqual(updated.name, "Modulo proteico atualizado")
        self.assertEqual(updated.protein_g, 25)
        self.assertEqual(updated.notes, "Atualizado")
        self.assertEqual(after_delete, [])


if __name__ == "__main__":
    unittest.main()
