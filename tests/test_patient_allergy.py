import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.schema import initialize_database
from nutri_app.domain.patient import Patient
from nutri_app.domain.patient_allergy import AllergyCategory, PatientAllergy
from nutri_app.repositories.patient_allergy_repository import PatientAllergyRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class PatientAllergyRepositoryTest(unittest.TestCase):
    def test_adiciona_e_lista_alergias_do_paciente(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            patient_id = PatientRepository(factory).add(
                Patient(name="Paciente Alergico", birth_date=date(1990, 1, 1))
            )
            repository = PatientAllergyRepository(factory)

            repository.add(
                PatientAllergy(
                    patient_id=patient_id,
                    category=AllergyCategory.FOOD,
                    allergen="Leite",
                    severity="Grave",
                    conduct="Evita completamente",
                )
            )
            repository.add(
                PatientAllergy(
                    patient_id=patient_id,
                    category=AllergyCategory.MEDICATION,
                    allergen="Antibioticos",
                )
            )

            allergies = repository.list_for_patient(patient_id)

        self.assertEqual(len(allergies), 2)
        self.assertEqual(
            {allergy.allergen for allergy in allergies}, {"Leite", "Antibioticos"}
        )
        food_allergy = next(a for a in allergies if a.allergen == "Leite")
        self.assertEqual(food_allergy.category, AllergyCategory.FOOD)
        self.assertEqual(food_allergy.severity, "Grave")

    def test_replace_for_patient_substitui_lista_anterior(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            patient_id = PatientRepository(factory).add(
                Patient(name="Paciente Alergico", birth_date=date(1990, 1, 1))
            )
            repository = PatientAllergyRepository(factory)
            repository.add(
                PatientAllergy(patient_id=patient_id, category=AllergyCategory.FOOD, allergen="Ovo")
            )

            repository.replace_for_patient(
                patient_id,
                [
                    PatientAllergy(
                        patient_id=patient_id, category=AllergyCategory.FOOD, allergen="Soja"
                    )
                ],
            )
            allergies = repository.list_for_patient(patient_id)

        self.assertEqual(len(allergies), 1)
        self.assertEqual(allergies[0].allergen, "Soja")


if __name__ == "__main__":
    unittest.main()
