from __future__ import annotations

from dataclasses import dataclass

from nutri_app.app.settings import AppSettings
from nutri_app.database.migrator import DatabaseMigrator
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


@dataclass(frozen=True)
class AppContext:
    settings: AppSettings
    connection_factory: SQLiteConnectionFactory


def build_app_context(settings: AppSettings) -> AppContext:
    connection_factory = SQLiteConnectionFactory(settings.database_path)
    migrator = DatabaseMigrator(connection_factory, settings.migrations_path)
    migrator.migrate()
    return AppContext(settings=settings, connection_factory=connection_factory)
