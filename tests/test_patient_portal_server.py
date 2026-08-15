import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.migrator import DatabaseMigrator
from nutri_app.domain.patient import Patient
from nutri_app.domain.patient_app import (
    PatientAppAccess,
    PatientAppPublication,
    PatientPublicationType,
)
from nutri_app.repositories.patient_app_repository import PatientAppRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.patient_portal_server import PatientPortalApplication


class PatientPortalApplicationTest(unittest.TestCase):
    def test_autentica_lista_publicacao_e_registra_adesao(self) -> None:
        with TemporaryDirectory() as tmp:
            factory = SQLiteConnectionFactory(Path(tmp) / "test.sqlite")
            DatabaseMigrator(factory, Path("database/migrations")).migrate()
            patient_id = PatientRepository(factory).add(
                Patient("Paciente Portal", date(1990, 1, 1))
            )
            repository = PatientAppRepository(factory)
            repository.upsert_access(
                PatientAppAccess(patient_id, "portal@example.com", "ABC12345")
            )
            publication_id = repository.add_publication(
                PatientAppPublication(
                    patient_id=patient_id,
                    publication_type=PatientPublicationType.MEAL_PLAN,
                    title="Plano",
                    content="Conteudo",
                )
            )
            app = PatientPortalApplication(factory)
            token = app.authenticate("portal@example.com", "ABC12345")
            publications = app.list_publications(token)
            adherence_id = app.record_adherence(token, publication_id, 85)

        self.assertEqual(publications[0]["titulo"], "Plano")
        self.assertGreater(adherence_id, 0)
