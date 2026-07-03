from __future__ import annotations

from datetime import datetime

from nutri_app.domain.user import Permission, User, UserRole
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class UserRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def count_users(self) -> int:
        with self.connection_factory.connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS total FROM usuarios WHERE deleted_at IS NULL"
            ).fetchone()
        return int(row["total"])

    def add(self, user: User) -> int:
        with self.connection_factory.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO usuarios (nome, email, senha_hash, perfil, ativo)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user.name,
                    user.email.strip().lower(),
                    user.password_hash,
                    user.role.value,
                    1 if user.active else 0,
                ),
            )
            return int(cursor.lastrowid)

    def list_active(self) -> list[User]:
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, nome, email, senha_hash, perfil, ativo, created_at, updated_at
                FROM usuarios
                WHERE deleted_at IS NULL
                ORDER BY nome
                """
            ).fetchall()
        return [self._row_to_user(row) for row in rows]

    def get_active_by_email(self, email: str) -> User | None:
        with self.connection_factory.connect() as connection:
            row = connection.execute(
                """
                SELECT id, nome, email, senha_hash, perfil, ativo, created_at, updated_at
                FROM usuarios
                WHERE lower(email) = lower(?) AND ativo = 1 AND deleted_at IS NULL
                """,
                (email.strip().lower(),),
            ).fetchone()
        return self._row_to_user(row) if row is not None else None

    def list_permissions_for_role(self, role: UserRole) -> list[Permission]:
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                """
                SELECT perfil, modulo, pode_visualizar, pode_criar, pode_editar,
                       pode_excluir, pode_exportar
                FROM perfis_permissao
                WHERE perfil = ?
                ORDER BY modulo
                """,
                (role.value,),
            ).fetchall()

        return [
            Permission(
                role=UserRole(row["perfil"]),
                module=row["modulo"],
                can_view=bool(row["pode_visualizar"]),
                can_create=bool(row["pode_criar"]),
                can_edit=bool(row["pode_editar"]),
                can_delete=bool(row["pode_excluir"]),
                can_export=bool(row["pode_exportar"]),
            )
            for row in rows
        ]

    def can_view_module(self, role: UserRole, module: str) -> bool:
        if role == UserRole.ADMINISTRADOR:
            return True

        with self.connection_factory.connect() as connection:
            row = connection.execute(
                """
                SELECT pode_visualizar
                FROM perfis_permissao
                WHERE perfil = ? AND modulo = ?
                """,
                (role.value, module),
            ).fetchone()
        return bool(row["pode_visualizar"]) if row is not None else False

    def _row_to_user(self, row) -> User:
        return User(
            id=row["id"],
            name=row["nome"],
            email=row["email"],
            password_hash=row["senha_hash"],
            role=UserRole(row["perfil"]),
            active=bool(row["ativo"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
