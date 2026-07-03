from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


@dataclass(frozen=True)
class Migration:
    version: str
    name: str
    path: Path


class DatabaseMigrator:
    def __init__(self, connection_factory: SQLiteConnectionFactory, migrations_path: Path) -> None:
        self.connection_factory = connection_factory
        self.migrations_path = migrations_path

    def migrate(self) -> list[Migration]:
        migrations = self._discover_migrations()
        applied: list[Migration] = []

        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            applied_versions = {
                row["version"]
                for row in connection.execute("SELECT version FROM schema_migrations").fetchall()
            }

            for migration in migrations:
                if migration.version in applied_versions:
                    continue

                connection.executescript(migration.path.read_text(encoding="utf-8"))
                connection.execute(
                    "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
                    (migration.version, migration.name),
                )
                applied.append(migration)

        return applied

    def _discover_migrations(self) -> list[Migration]:
        if not self.migrations_path.exists():
            return []

        migrations: list[Migration] = []
        for path in sorted(self.migrations_path.glob("*.sql")):
            version, _, name = path.stem.partition("_")
            if not version.isdigit() or not name:
                raise ValueError(f"Migration invalida: {path.name}")
            migrations.append(Migration(version=version, name=name, path=path))
        return migrations
