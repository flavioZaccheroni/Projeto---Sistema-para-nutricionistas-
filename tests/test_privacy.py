import json
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.migrator import DatabaseMigrator
from nutri_app.domain.patient import Patient
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.privacy import PatientPrivacyService


class PatientPrivacyServiceTest(unittest.TestCase):
    def test_consentimento_e_exportacao_preservam_dados_relacionados(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            factory = SQLiteConnectionFactory(root / "test.sqlite")
            DatabaseMigrator(factory, Path("database/migrations")).migrate()
            patient_id = PatientRepository(factory).add(
                Patient("Paciente LGPD", date(1990, 1, 1), email="pessoa@example.com")
            )
            service = PatientPrivacyService(factory)
            consent_id = service.record_consent(patient_id, "1.0", True, 1)
            result = service.export_patient_data(patient_id, root / "exports")
            payload = json.loads(result.file_path.read_text(encoding="utf-8"))

        self.assertGreater(consent_id, 0)
        self.assertEqual(payload["metadata"]["patient_id"], patient_id)
        self.assertEqual(payload["data"]["pacientes"][0]["email"], "pessoa@example.com")

    def test_anonimizacao_remove_identificadores_sem_apagar_prontuario(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            factory = SQLiteConnectionFactory(root / "test.sqlite")
            DatabaseMigrator(factory, Path("database/migrations")).migrate()
            repository = PatientRepository(factory)
            patient_id = repository.add(
                Patient("Nome Sensivel", date(1980, 2, 3), document="529.982.247-25")
            )
            PatientPrivacyService(factory).anonymize_patient(
                patient_id, "Solicitacao validada do titular"
            )
            patient = repository.get(patient_id)

        self.assertIsNotNone(patient)
        self.assertIn("anonimizado", patient.name)
        self.assertEqual(patient.document, "")


if __name__ == "__main__":
    unittest.main()
