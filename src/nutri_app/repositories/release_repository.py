from __future__ import annotations

import ast
from datetime import datetime
from pathlib import Path

from nutri_app.domain.release import ReleaseCheck, ReleaseCheckStatus
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class ReleaseRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory, project_root: Path) -> None:
        self.connection_factory = connection_factory
        self.project_root = project_root

    def collect_metrics(self, tests_count: int | None = None) -> dict[str, object]:
        with self.connection_factory.connect() as connection:
            migrations = connection.execute(
                "SELECT COUNT(*) AS total FROM schema_migrations"
            ).fetchone()
            permissions = connection.execute(
                "SELECT COUNT(*) AS total FROM perfis_permissao"
            ).fetchone()
            admin = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM usuarios
                WHERE perfil = 'Administrador' AND ativo = 1 AND deleted_at IS NULL
                """
            ).fetchone()
            backup_config = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM configuracoes
                WHERE chave = 'backup_diretorio_padrao' AND deleted_at IS NULL
                """
            ).fetchone()
            portal_config = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM configuracoes
                WHERE chave = 'portal_web_diretorio_padrao' AND deleted_at IS NULL
                """
            ).fetchone()
        phase_docs = len(list((self.project_root / "docs" / "fases").glob("fase_*.md")))
        return {
            "migrations": int(migrations["total"]),
            "permissions": int(permissions["total"]),
            "phase_docs": phase_docs,
            "tests": tests_count if tests_count is not None else self._count_tests(),
            "has_admin": int(admin["total"]) > 0,
            "has_backup_config": int(backup_config["total"]) > 0,
            "has_web_portal": int(portal_config["total"]) > 0,
            "has_icon": (self.project_root / "icone.png").exists(),
        }

    def replace_checks(self, checks: list[ReleaseCheck]) -> None:
        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE implantacao_checks
                SET deleted_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE deleted_at IS NULL
                """
            )
            for check in checks:
                connection.execute(
                    """
                    INSERT INTO implantacao_checks (nome, status, detalhes)
                    VALUES (?, ?, ?)
                    """,
                    (check.name, check.status.value, check.details),
                )

    def list_checks(self) -> list[ReleaseCheck]:
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, nome, status, detalhes, created_at, updated_at
                FROM implantacao_checks
                WHERE deleted_at IS NULL
                ORDER BY id
                """
            ).fetchall()
        return [
            ReleaseCheck(
                id=row["id"],
                name=row["nome"],
                status=ReleaseCheckStatus(row["status"]),
                details=row["detalhes"] or "",
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
            for row in rows
        ]

    def _count_tests(self) -> int:
        total = 0
        for path in (self.project_root / "tests").glob("test_*.py"):
            module = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(module):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    total += 1
        return total
