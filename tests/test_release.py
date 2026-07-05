import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.migrator import DatabaseMigrator
from nutri_app.domain.release import ReleaseCheck, ReleaseCheckStatus
from nutri_app.domain.user import User, UserRole
from nutri_app.repositories.release_repository import ReleaseRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.repositories.user_repository import UserRepository
from nutri_app.services.release import ReleaseService


class ReleaseServiceTest(unittest.TestCase):
    def test_avalia_release_pronta_quando_todos_checks_passam(self) -> None:
        metrics = {
            "migrations": 18,
            "tests": 66,
            "phase_docs": 24,
            "permissions": 1,
            "has_admin": True,
            "has_icon": True,
            "has_backup_config": True,
            "has_web_portal": True,
        }

        readiness = ReleaseService().evaluate(metrics, "1.0.0")
        summary = ReleaseService().release_summary(readiness)

        self.assertTrue(readiness.ready)
        self.assertEqual(readiness.total_passed, len(readiness.checks))
        self.assertIn("Nutri Clinic Pro v1.0.0 pronto", summary)


class ReleaseRepositoryTest(unittest.TestCase):
    def test_coleta_metricas_e_persiste_checks_de_implantacao(self) -> None:
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
            UserRepository(factory).add(
                User(
                    name="Administrador",
                    email="admin@test.local",
                    password_hash="hash",
                    role=UserRole.ADMINISTRADOR,
                )
            )
            repository = ReleaseRepository(factory, Path.cwd())

            metrics = repository.collect_metrics(tests_count=66)
            repository.replace_checks(
                [
                    ReleaseCheck(
                        "Migrations aplicadas",
                        ReleaseCheckStatus.PASSED,
                        "18 encontrado(s).",
                    )
                ]
            )
            checks = repository.list_checks()

        self.assertGreaterEqual(metrics["migrations"], 18)
        self.assertGreaterEqual(metrics["phase_docs"], 24)
        self.assertTrue(metrics["has_admin"])
        self.assertTrue(metrics["has_backup_config"])
        self.assertTrue(metrics["has_web_portal"])
        self.assertEqual(len(checks), 1)
        self.assertEqual(checks[0].status, ReleaseCheckStatus.PASSED)


if __name__ == "__main__":
    unittest.main()
