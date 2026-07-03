from __future__ import annotations

from dataclasses import dataclass

from nutri_app.app.settings import AppSettings
from nutri_app.database.migrator import DatabaseMigrator
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.repositories.user_repository import UserRepository
from nutri_app.services.auth import AuthService


@dataclass(frozen=True)
class AppContext:
    settings: AppSettings
    connection_factory: SQLiteConnectionFactory
    user_repository: UserRepository
    audit_repository: AuditRepository
    auth_service: AuthService


def build_app_context(settings: AppSettings) -> AppContext:
    connection_factory = SQLiteConnectionFactory(settings.database_path)
    migrator = DatabaseMigrator(connection_factory, settings.migrations_path)
    migrator.migrate()
    user_repository = UserRepository(connection_factory)
    audit_repository = AuditRepository(connection_factory)
    auth_service = AuthService(user_repository, audit_repository)
    auth_service.ensure_default_admin()
    return AppContext(
        settings=settings,
        connection_factory=connection_factory,
        user_repository=user_repository,
        audit_repository=audit_repository,
        auth_service=auth_service,
    )
