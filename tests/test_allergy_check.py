import unittest

from nutri_app.domain.food import Food, FoodSource
from nutri_app.domain.patient_allergy import AllergyCategory, PatientAllergy
from nutri_app.services.allergy_check import AllergyCheckService


class AllergyCheckServiceTest(unittest.TestCase):
    def test_identifica_conflito_pelo_nome_do_alimento(self) -> None:
        allergies = [
            PatientAllergy(patient_id=1, category=AllergyCategory.FOOD, allergen="Iogurte")
        ]
        food = Food(name="Iogurte natural integral", source=FoodSource.REGIONAL)

        conflicts = AllergyCheckService().find_conflicts(allergies, food)

        self.assertEqual(conflicts, ["Iogurte"])

    def test_identifica_conflito_pela_categoria(self) -> None:
        allergies = [
            PatientAllergy(patient_id=1, category=AllergyCategory.FOOD, allergen="Laticinios")
        ]
        food = Food(
            name="Queijo mussarela", source=FoodSource.REGIONAL, category="Laticinios"
        )

        conflicts = AllergyCheckService().find_conflicts(allergies, food)

        self.assertEqual(conflicts, ["Laticinios"])

    def test_identifica_conflito_pela_tag_de_alergenos(self) -> None:
        allergies = [
            PatientAllergy(patient_id=1, category=AllergyCategory.FOOD, allergen="Gluten")
        ]
        food = Food(
            name="Pao de trigo", source=FoodSource.REGIONAL, allergens="gluten,trigo"
        )

        conflicts = AllergyCheckService().find_conflicts(allergies, food)

        self.assertEqual(conflicts, ["Gluten"])

    def test_sem_conflito_quando_nao_ha_correspondencia(self) -> None:
        allergies = [
            PatientAllergy(patient_id=1, category=AllergyCategory.FOOD, allergen="Amendoim")
        ]
        food = Food(name="Arroz branco", source=FoodSource.REGIONAL, category="Cereais")

        conflicts = AllergyCheckService().find_conflicts(allergies, food)

        self.assertEqual(conflicts, [])


if __name__ == "__main__":
    unittest.main()
