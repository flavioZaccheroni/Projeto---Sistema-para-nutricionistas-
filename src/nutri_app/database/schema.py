from __future__ import annotations

from pathlib import Path

from nutri_app.database.migrator import DatabaseMigrator
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


def initialize_database(connection_factory: SQLiteConnectionFactory) -> None:
    root = Path(__file__).resolve().parents[3]
    DatabaseMigrator(connection_factory, root / "database" / "migrations").migrate()
