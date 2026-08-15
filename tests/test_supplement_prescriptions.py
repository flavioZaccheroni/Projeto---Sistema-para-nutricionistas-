import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.schema import initialize_database
from nutri_app.domain.patient import Patient
from nutri_app.domain.supplement import Supplement, SupplementType
from nutri_app.domain.supplement_prescription import SupplementFollowUp, SupplementPrescription
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.repositories.supplement_prescription_repository import (
    SupplementPrescriptionRepository,
)
from nutri_app.repositories.supplement_repository import SupplementRepository


class SupplementPrescriptionRepositoryTest(unittest.TestCase):
    def test_prescricao_congela_produto_calcula_aporte_e_registra_adesao(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            patient_id = PatientRepository(factory).add(Patient("Paciente", date(1990, 1, 1)))
            supplement_repository = SupplementRepository(factory)
            supplement_id = supplement_repository.add(
                Supplement(
                    name="Modulo proteico",
                    supplement_type=SupplementType.PROTEIN_MODULE,
                    base_portion=30,
                    portion_unit="g",
                    energy_kcal=120,
                    protein_g=24,
                )
            )
            repository = SupplementPrescriptionRepository(factory)
            prescription_id = repository.add(
                SupplementPrescription(
                    patient_id=patient_id,
                    supplement_id=supplement_id,
                    start_date=date(2026, 8, 15),
                    end_date=date(2026, 9, 15),
                    quantity=30,
                    unit="g",
                    frequency_per_day=2,
                    times="08:00, 16:00",
                    objective="Atingir meta proteica",
                    instructions="Diluir em 200 ml e administrar apos as refeicoes.",
                )
            )
            supplement_repository.update(
                Supplement(
                    id=supplement_id,
                    name="Produto alterado no catalogo",
                    supplement_type=SupplementType.PROTEIN_MODULE,
                    base_portion=30,
                    portion_unit="g",
                    energy_kcal=90,
                    protein_g=18,
                )
            )
            repository.add_follow_up(
                SupplementFollowUp(
                    prescription_id=prescription_id,
                    record_date=date(2026, 8, 20),
                    acceptance=8,
                    adherence_percent=90,
                    clinical_response="Boa tolerancia.",
                )
            )
            prescription = repository.get(prescription_id)
            follow_ups = repository.list_follow_ups(prescription_id)

        self.assertEqual(prescription.supplement_name, "Modulo proteico")
        self.assertAlmostEqual(prescription.daily_intake["proteina_g"], 48)
        self.assertEqual(follow_ups[0].acceptance, 8)

    def test_suspensao_e_validacoes_clinicas(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            initialize_database(factory)
            patient_id = PatientRepository(factory).add(Patient("Paciente", date(1990, 1, 1)))
            supplement_id = SupplementRepository(factory).add(
                Supplement("Produto", SupplementType.OTHER, base_portion=10, portion_unit="g")
            )
            repository = SupplementPrescriptionRepository(factory)
            prescription_id = repository.add(
                SupplementPrescription(
                    patient_id,
                    supplement_id,
                    date(2026, 8, 15),
                    date(2026, 8, 30),
                    10,
                    "g",
                    1,
                    "10:00",
                    "Complementacao",
                    "Administrar conforme tolerancia.",
                )
            )
            repository.add_follow_up(
                SupplementFollowUp(
                    prescription_id,
                    date(2026, 8, 18),
                    2,
                    40,
                    incidents="Nausea",
                    suspension_reason="Intolerancia gastrointestinal persistente",
                )
            )

            suspended = repository.get(prescription_id)
            with self.assertRaises(ValueError):
                repository.add_follow_up(
                    SupplementFollowUp(prescription_id, date(2026, 8, 19), 11, 50)
                )

        self.assertEqual(suspended.status, "Suspensa")


if __name__ == "__main__":
    unittest.main()
