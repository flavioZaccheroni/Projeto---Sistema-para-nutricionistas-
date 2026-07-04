import unittest
from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.schema import initialize_database
from nutri_app.domain.appointment import Appointment, AppointmentKind, AppointmentStatus
from nutri_app.domain.meal_plan import Meal, MealPlan, MealPlanItem
from nutri_app.domain.patient import Patient
from nutri_app.repositories.appointment_repository import AppointmentRepository
from nutri_app.repositories.meal_plan_repository import MealPlanRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.meal_plan import MealPlanService


class MealPlanServiceTest(unittest.TestCase):
    def test_calcula_totais_e_lista_de_compras(self) -> None:
        service = MealPlanService()
        meals = [
            Meal(
                name="Cafe da manha",
                items=[
                    MealPlanItem(
                        "Aveia",
                        40,
                        "g",
                        energy_kcal=150,
                        protein_g=5,
                        carbohydrate_g=27,
                        fat_g=3,
                    ),
                    MealPlanItem("Banana", 1, "un", energy_kcal=90, protein_g=1, carbohydrate_g=23),
                ],
            ),
            Meal(
                name="Lanche",
                items=[
                    MealPlanItem(
                        "Aveia",
                        20,
                        "g",
                        energy_kcal=75,
                        protein_g=2.5,
                        carbohydrate_g=13.5,
                        fat_g=1.5,
                    )
                ],
            ),
        ]

        totals = service.calculate_totals(meals)
        shopping = service.build_shopping_list(meals)

        self.assertEqual(totals, (315, 8.5, 63.5, 4.5))
        self.assertIn("aveia: 60 g", shopping)
        self.assertIn("banana: 1 un", shopping)

    def test_rejeita_plano_sem_refeicao_valida(self) -> None:
        with self.assertRaises(ValueError):
            MealPlanService().validate_plan(
                MealPlan(patient_id=1, start_date=date.today(), objective="Meta")
            )


class MealPlanRepositoryTest(unittest.TestCase):
    def test_cria_lista_atualiza_e_exclui_plano_alimentar(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            patient_id = PatientRepository(factory).add(
                Patient(name="Paciente Plano", birth_date=date(1992, 8, 1))
            )
            appointment_id = AppointmentRepository(factory).add(
                Appointment(
                    patient_id=patient_id,
                    scheduled_at=datetime(2026, 7, 13, 14, 0),
                    kind=AppointmentKind.FOLLOW_UP,
                    status=AppointmentStatus.SCHEDULED,
                )
            )
            repository = MealPlanRepository(factory)

            plan_id = repository.add(
                MealPlan(
                    patient_id=patient_id,
                    appointment_id=appointment_id,
                    start_date=date(2026, 7, 13),
                    objective="Perda de peso",
                    target_energy_kcal=1800,
                    total_energy_kcal=520,
                    total_protein_g=35,
                    total_carbohydrate_g=60,
                    total_fat_g=16,
                    meals=[
                        Meal(
                            name="Almoco",
                            time="12:00",
                            items=[
                                MealPlanItem(
                                    "Arroz",
                                    120,
                                    "g",
                                    energy_kcal=160,
                                    protein_g=3,
                                    carbohydrate_g=35,
                                    fat_g=1,
                                ),
                                MealPlanItem(
                                    "Frango",
                                    150,
                                    "g",
                                    energy_kcal=360,
                                    protein_g=32,
                                    carbohydrate_g=25,
                                    fat_g=15,
                                ),
                            ],
                        )
                    ],
                )
            )
            listed = repository.list_active("plano")
            loaded = repository.get(plan_id)
            repository.update(
                MealPlan(
                    id=plan_id,
                    patient_id=patient_id,
                    appointment_id=appointment_id,
                    start_date=date(2026, 7, 14),
                    objective="Manutencao",
                    total_energy_kcal=300,
                    total_protein_g=20,
                    total_carbohydrate_g=30,
                    total_fat_g=8,
                    meals=[
                        Meal(
                            name="Jantar",
                            time="19:00",
                            items=[
                                MealPlanItem(
                                    "Omelete",
                                    1,
                                    "porcao",
                                    energy_kcal=300,
                                    protein_g=20,
                                    carbohydrate_g=30,
                                    fat_g=8,
                                )
                            ],
                        )
                    ],
                    notes="Atualizado",
                )
            )
            updated = repository.get(plan_id)
            repository.soft_delete(plan_id)
            after_delete = repository.list_active()

        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].patient_name, "Paciente Plano")
        self.assertEqual(len(loaded.meals), 1)
        self.assertEqual(len(loaded.meals[0].items), 2)
        self.assertEqual(updated.objective, "Manutencao")
        self.assertEqual(updated.meals[0].name, "Jantar")
        self.assertEqual(updated.notes, "Atualizado")
        self.assertEqual(after_delete, [])


if __name__ == "__main__":
    unittest.main()
