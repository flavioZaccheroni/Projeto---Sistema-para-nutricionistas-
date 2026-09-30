import unittest
from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.schema import initialize_database
from nutri_app.domain.appointment import Appointment, AppointmentKind, AppointmentStatus
from nutri_app.domain.body_composition import BodyComposition, BodyCompositionProtocol
from nutri_app.domain.energy_expenditure import BiologicalSex
from nutri_app.domain.patient import Patient
from nutri_app.repositories.appointment_repository import AppointmentRepository
from nutri_app.repositories.body_composition_repository import BodyCompositionRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.body_composition import BodyCompositionService
from nutri_app.services.body_fat_calculation import (
    BodyFatCalculationService,
    SkinfoldProtocol,
    SkinfoldSite,
)


class BodyCompositionServiceTest(unittest.TestCase):
    def test_calcula_massa_gorda_e_massa_magra(self) -> None:
        service = BodyCompositionService()

        self.assertAlmostEqual(service.calculate_fat_mass(80, 25), 20)
        self.assertAlmostEqual(service.calculate_lean_mass(80, 25), 60)

    def test_rejeita_valores_invalidos(self) -> None:
        service = BodyCompositionService()

        with self.assertRaises(ValueError):
            service.calculate_fat_mass(0, 20)
        with self.assertRaises(ValueError):
            service.calculate_lean_mass(80, 101)


class BodyFatCalculationServiceTest(unittest.TestCase):
    def test_pollock_3_dobras_homem(self) -> None:
        service = BodyFatCalculationService()

        percentage = service.calculate_body_fat_percentage(
            SkinfoldProtocol.POLLOCK_3,
            BiologicalSex.MALE,
            20,
            {
                SkinfoldSite.CHEST: 10,
                SkinfoldSite.ABDOMEN: 15,
                SkinfoldSite.THIGH: 12,
            },
        )

        self.assertAlmostEqual(percentage, 10.11, places=1)

    def test_pollock_7_dobras_homem(self) -> None:
        service = BodyFatCalculationService()

        percentage = service.calculate_body_fat_percentage(
            SkinfoldProtocol.POLLOCK_7,
            BiologicalSex.MALE,
            25,
            {
                SkinfoldSite.CHEST: 15,
                SkinfoldSite.MIDAXILLARY: 10,
                SkinfoldSite.TRICEPS: 12,
                SkinfoldSite.SUBSCAPULAR: 15,
                SkinfoldSite.ABDOMEN: 20,
                SkinfoldSite.SUPRAILIAC: 18,
                SkinfoldSite.THIGH: 10,
            },
        )

        self.assertAlmostEqual(percentage, 14.01, places=1)

    def test_durnin_womersley_homem(self) -> None:
        service = BodyFatCalculationService()

        percentage = service.calculate_body_fat_percentage(
            SkinfoldProtocol.DURNIN_WOMERSLEY,
            BiologicalSex.MALE,
            25,
            {
                SkinfoldSite.BICEPS: 8,
                SkinfoldSite.TRICEPS: 12,
                SkinfoldSite.SUBSCAPULAR: 15,
                SkinfoldSite.SUPRAILIAC: 18,
            },
        )

        self.assertAlmostEqual(percentage, 19.58, places=1)

    def test_faulkner_formula_direta(self) -> None:
        service = BodyFatCalculationService()

        percentage = service.calculate_body_fat_percentage(
            SkinfoldProtocol.FAULKNER,
            BiologicalSex.FEMALE,
            30,
            {
                SkinfoldSite.TRICEPS: 12,
                SkinfoldSite.SUBSCAPULAR: 15,
                SkinfoldSite.SUPRAILIAC: 18,
                SkinfoldSite.ABDOMEN: 20,
            },
        )

        self.assertAlmostEqual(percentage, 15.728, places=2)

    def test_rejeita_dobra_faltante(self) -> None:
        service = BodyFatCalculationService()

        with self.assertRaises(ValueError):
            service.calculate_body_fat_percentage(
                SkinfoldProtocol.POLLOCK_3,
                BiologicalSex.MALE,
                20,
                {SkinfoldSite.CHEST: 10, SkinfoldSite.ABDOMEN: 15},
            )

    def test_rejeita_idade_invalida(self) -> None:
        service = BodyFatCalculationService()

        with self.assertRaises(ValueError):
            service.calculate_body_fat_percentage(
                SkinfoldProtocol.FAULKNER,
                BiologicalSex.FEMALE,
                0,
                {
                    SkinfoldSite.TRICEPS: 12,
                    SkinfoldSite.SUBSCAPULAR: 15,
                    SkinfoldSite.SUPRAILIAC: 18,
                    SkinfoldSite.ABDOMEN: 20,
                },
            )


class BodyCompositionRepositoryTest(unittest.TestCase):
    def test_cria_lista_atualiza_e_exclui_composicao_corporal(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            patient_id = PatientRepository(factory).add(
                Patient(name="Paciente Composicao", birth_date=date(1988, 4, 12))
            )
            appointment_id = AppointmentRepository(factory).add(
                Appointment(
                    patient_id=patient_id,
                    scheduled_at=datetime(2026, 7, 8, 9, 0),
                    kind=AppointmentKind.FIRST_VISIT,
                    status=AppointmentStatus.SCHEDULED,
                )
            )
            repository = BodyCompositionRepository(factory)

            composition_id = repository.add(
                BodyComposition(
                    patient_id=patient_id,
                    appointment_id=appointment_id,
                    assessment_date=date(2026, 7, 8),
                    protocol=BodyCompositionProtocol.BIA,
                    weight_kg=80,
                    body_fat_percentage=25,
                    fat_mass_kg=20,
                    lean_mass_kg=60,
                    body_water_percentage=52,
                    muscle_mass_kg=35,
                    visceral_fat=8,
                    notes="Bioimpedancia inicial",
                )
            )
            listed = repository.list_active("composicao")
            repository.update(
                BodyComposition(
                    id=composition_id,
                    patient_id=patient_id,
                    appointment_id=appointment_id,
                    assessment_date=date(2026, 7, 9),
                    protocol=BodyCompositionProtocol.POLLOCK,
                    weight_kg=79,
                    body_fat_percentage=24,
                    fat_mass_kg=18.96,
                    lean_mass_kg=60.04,
                    body_water_percentage=53,
                    muscle_mass_kg=36,
                    visceral_fat=7,
                    notes="Atualizado",
                )
            )
            updated = repository.get(composition_id)
            repository.soft_delete(composition_id)
            after_delete = repository.list_active()

        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].patient_name, "Paciente Composicao")
        self.assertIn("Consulta inicial", listed[0].appointment_label)
        self.assertEqual(updated.protocol, BodyCompositionProtocol.POLLOCK)
        self.assertAlmostEqual(updated.fat_mass_kg, 18.96)
        self.assertEqual(updated.notes, "Atualizado")
        self.assertEqual(after_delete, [])


if __name__ == "__main__":
    unittest.main()
