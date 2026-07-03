import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.migrator import DatabaseMigrator
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class DatabaseMigratorTest(unittest.TestCase):
    def test_executa_migrations_uma_unica_vez(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            migrations_path = root / "migrations"
            migrations_path.mkdir()
            (migrations_path / "0001_test.sql").write_text(
                "CREATE TABLE exemplo (id INTEGER PRIMARY KEY);",
                encoding="utf-8",
            )

            factory = SQLiteConnectionFactory(root / "test.sqlite")
            migrator = DatabaseMigrator(factory, migrations_path)

            first_run = migrator.migrate()
            second_run = migrator.migrate()

            with factory.connect() as connection:
                row = connection.execute(
                    "SELECT COUNT(*) AS total FROM schema_migrations"
                ).fetchone()

        self.assertEqual(len(first_run), 1)
        self.assertEqual(len(second_run), 0)
        self.assertEqual(row["total"], 1)


if __name__ == "__main__":
    unittest.main()
