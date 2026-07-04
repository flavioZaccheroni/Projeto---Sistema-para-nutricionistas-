import unittest
from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.schema import initialize_database
from nutri_app.domain.appointment import Appointment, AppointmentKind, AppointmentStatus
from nutri_app.domain.energy_expenditure import (
    BiologicalSex,
    EnergyEquation,
    EnergyExpenditure,
)
from nutri_app.domain.patient import Patient
from nutri_app.repositories.appointment_repository import AppointmentRepository
from nutri_app.repositories.energy_expenditure_repository import EnergyExpenditureRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.energy_expenditure import EnergyExpenditureService


class EnergyExpenditureServiceTest(unittest.TestCase):
    def test_calcula_mifflin_get_e_macros(self) -> None:
        service = EnergyExpenditureService()

        basal = service.calculate_basal_energy(
            EnergyEquation.MIFFLIN_ST_JEOR,
            BiologicalSex.MALE,
            age_years=30,
            weight_kg=80,
            height_cm=180,
        )
        total = service.calculate_total_energy(
            basal,
            activity_factor=1.3,
            stress_factor=1.0,
            equation=EnergyEquation.MIFFLIN_ST_JEOR,
        )
        macros = service.calculate_macronutrients(
            total,
            80,
            protein_g_per_kg=1.2,
            fat_percentage=30,
        )

        self.assertAlmostEqual(basal, 1780)
        self.assertAlmostEqual(total, 2314)
        self.assertAlmostEqual(macros.protein_g, 96)
        self.assertAlmostEqual(macros.fat_g, 77.13, places=2)
        self.assertAlmostEqual(macros.carbohydrate_g, 308.95, places=2)

    def test_cunningham_exige_massa_magra(self) -> None:
        with self.assertRaises(ValueError):
            EnergyExpenditureService().calculate_basal_energy(
                EnergyEquation.CUNNINGHAM,
                BiologicalSex.FEMALE,
                age_years=35,
                weight_kg=60,
                height_cm=165,
            )


class EnergyExpenditureRepositoryTest(unittest.TestCase):
    def test_cria_lista_atualiza_e_exclui_gasto_energetico(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            patient_id = PatientRepository(factory).add(
                Patient(name="Paciente Energia", birth_date=date(1991, 5, 20))
            )
            appointment_id = AppointmentRepository(factory).add(
                Appointment(
                    patient_id=patient_id,
                    scheduled_at=datetime(2026, 7, 9, 10, 0),
                    kind=AppointmentKind.FIRST_VISIT,
                    status=AppointmentStatus.SCHEDULED,
                )
            )
            repository = EnergyExpenditureRepository(factory)

            expenditure_id = repository.add(
                EnergyExpenditure(
                    patient_id=patient_id,
                    appointment_id=appointment_id,
                    assessment_date=date(2026, 7, 9),
                    sex=BiologicalSex.FEMALE,
                    age_years=35,
                    weight_kg=62,
                    height_cm=165,
                    lean_mass_kg=45,
                    equation=EnergyEquation.KATCH_MCARDLE,
                    activity_factor=1.35,
                    stress_factor=1.0,
                    goal_adjustment_kcal=0,
                    basal_energy_kcal=1342,
                    total_energy_kcal=1811.7,
                    protein_g=74.4,
                    carbohydrate_g=286.2,
                    fat_g=50.3,
                    notes="Estimativa inicial",
                )
            )
            listed = repository.list_active("energia")
            repository.update(
                EnergyExpenditure(
                    id=expenditure_id,
                    patient_id=patient_id,
                    appointment_id=appointment_id,
                    assessment_date=date(2026, 7, 10),
                    sex=BiologicalSex.FEMALE,
                    age_years=35,
                    weight_kg=61,
                    height_cm=165,
                    lean_mass_kg=45,
                    equation=EnergyEquation.MIFFLIN_ST_JEOR,
                    activity_factor=1.4,
                    stress_factor=1.0,
                    goal_adjustment_kcal=-200,
                    basal_energy_kcal=1295.25,
                    total_energy_kcal=1613.35,
                    protein_g=73.2,
                    carbohydrate_g=208.0,
                    fat_g=53.8,
                    notes="Atualizado",
                )
            )
            updated = repository.get(expenditure_id)
            repository.soft_delete(expenditure_id)
            after_delete = repository.list_active()

        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].patient_name, "Paciente Energia")
        self.assertIn("Consulta inicial", listed[0].appointment_label)
        self.assertEqual(updated.equation, EnergyEquation.MIFFLIN_ST_JEOR)
        self.assertAlmostEqual(updated.total_energy_kcal, 1613.35)
        self.assertEqual(updated.notes, "Atualizado")
        self.assertEqual(after_delete, [])


if __name__ == "__main__":
    unittest.main()
