import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.migrator import DatabaseMigrator
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.repositories.user_repository import UserRepository
from nutri_app.services.auth import AuthService
from nutri_app.services.security import PasswordHasher


class AuthServiceTest(unittest.TestCase):
    def test_cria_admin_padrao_e_autentica(self) -> None:
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
            users = UserRepository(factory)
            auth = AuthService(users, AuditRepository(factory))

            auth.ensure_default_admin()
            result = auth.login("admin@nutricionistas.local", "Admin@123")

        self.assertIsNotNone(result.user)
        self.assertEqual(result.user.email, "admin@nutricionistas.local")


class PasswordHasherTest(unittest.TestCase):
    def test_hash_nao_armazena_senha_em_texto_puro(self) -> None:
        hasher = PasswordHasher()

        password_hash = hasher.hash_password("Senha@123")

        self.assertNotIn("Senha@123", password_hash)
        self.assertTrue(hasher.verify_password("Senha@123", password_hash))
        self.assertFalse(hasher.verify_password("senha_errada", password_hash))


if __name__ == "__main__":
    unittest.main()
