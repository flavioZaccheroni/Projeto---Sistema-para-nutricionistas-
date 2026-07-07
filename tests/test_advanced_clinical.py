import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.migrator import DatabaseMigrator
from nutri_app.domain.advanced_clinical import AdvancedClinicalRecord
from nutri_app.domain.patient import Patient
from nutri_app.repositories.advanced_clinical_repository import AdvancedClinicalRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.advanced_clinical import AdvancedClinicalService
from nutri_app.ui.date_format import format_date, parse_date


class AdvancedClinicalServiceTest(unittest.TestCase):
    def test_avalia_modulos_das_fases_26_a_33(self) -> None:
        service = AdvancedClinicalService()
        definitions = service.definitions()

        self.assertEqual([definition.phase for definition in definitions], list(range(26, 34)))
        self.assertIn(
            "hipercalemia",
            service.evaluate_advanced_labs("Adulto", {"potassium": "5.8"}, ""),
        )
        self.assertIn(
            "desnutricao",
            service.evaluate_protocols(
                "BRASPEN",
                {"phenotypic": "2", "etiologic": "1", "muscle_loss": "1"},
                "",
            ),
        )
        self.assertIn(
            "URR",
            service.evaluate_nephrology(
                "Hemodialise",
                {
                    "dry_weight": "70",
                    "pre_weight": "73",
                    "pre_urea": "120",
                    "post_urea": "35",
                    "session_hours": "4",
                    "ultrafiltration": "3",
                },
                "",
            ),
        )
        self.assertIn(
            "volume",
            service.evaluate_nutrition_therapy(
                "Enteral",
                {
                    "energy_target": "1800",
                    "protein_target": "90",
                    "formula_density": "1.2",
                    "formula_protein": "5",
                    "infusion_hours": "20",
                    "water_flush": "600",
                },
                "",
            ),
        )

    def test_formato_visual_de_data_mm_dd_aaaa(self) -> None:
        parsed = parse_date("07-07-2026")

        self.assertEqual(parsed, date(2026, 7, 7))
        self.assertEqual(format_date(parsed), "07-07-2026")


class AdvancedClinicalRepositoryTest(unittest.TestCase):
    def test_persiste_registro_avancado(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            migrations = root / "migrations"
            migrations.mkdir()
            source = Path("database/migrations")
            for migration in source.glob("*.sql"):
                (migrations / migration.name).write_text(
                    migration.read_text(encoding="utf-8"),
                    encoding="utf-8",
                )

            factory = SQLiteConnectionFactory(root / "test.sqlite")
            DatabaseMigrator(factory, migrations).migrate()
            patient_id = PatientRepository(factory).add(
                Patient(name="Paciente Avancado", birth_date=date(1990, 1, 1))
            )
            repository = AdvancedClinicalRepository(factory)

            record_id = repository.add(
                AdvancedClinicalRecord(
                    module="Pediatria",
                    patient_id=patient_id,
                    record_date=date(2026, 7, 7),
                    profile="Crianca",
                    inputs={"percentile": "50"},
                    result="faixa esperada",
                    notes="teste",
                )
            )
            records = repository.list_by_module("Pediatria")

        self.assertGreater(record_id, 0)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].patient_name, "Paciente Avancado")
        self.assertEqual(records[0].inputs["percentile"], "50")


if __name__ == "__main__":
    unittest.main()
