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
                INSERT INTO usuarios (
                    nome, email, senha_hash, perfil, ativo, troca_senha_obrigatoria,
                    tentativas_falhas, bloqueado_ate, senha_alterada_em
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user.name,
                    user.email.strip().lower(),
                    user.password_hash,
                    user.role.value,
                    1 if user.active else 0,
                    1 if user.must_change_password else 0,
                    user.failed_login_attempts,
                    user.locked_until.isoformat() if user.locked_until else None,
                    user.password_changed_at.isoformat() if user.password_changed_at else None,
                ),
            )
            return int(cursor.lastrowid)

    def list_active(self) -> list[User]:
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, nome, email, senha_hash, perfil, ativo, troca_senha_obrigatoria,
                       tentativas_falhas, bloqueado_ate, senha_alterada_em,
                       created_at, updated_at
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
                SELECT id, nome, email, senha_hash, perfil, ativo, troca_senha_obrigatoria,
                       tentativas_falhas, bloqueado_ate, senha_alterada_em,
                       created_at, updated_at
                FROM usuarios
                WHERE lower(email) = lower(?) AND ativo = 1 AND deleted_at IS NULL
                """,
                (email.strip().lower(),),
            ).fetchone()
        return self._row_to_user(row) if row is not None else None

    def register_failed_login(self, user_id: int, max_attempts: int, lock_minutes: int) -> None:
        with self.connection_factory.connect() as connection:
            row = connection.execute(
                "SELECT tentativas_falhas FROM usuarios WHERE id = ?",
                (user_id,),
            ).fetchone()
            attempts = int(row["tentativas_falhas"] or 0) + 1
            locked_until = None
            if attempts >= max_attempts:
                from datetime import timedelta

                locked_until = (datetime.now() + timedelta(minutes=lock_minutes)).isoformat()
                attempts = 0
            connection.execute(
                """
                UPDATE usuarios
                SET tentativas_falhas = ?, bloqueado_ate = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (attempts, locked_until, user_id),
            )

    def clear_login_failures(self, user_id: int) -> None:
        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE usuarios
                SET tentativas_falhas = 0, bloqueado_ate = NULL, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (user_id,),
            )

    def change_password(self, user_id: int, password_hash: str) -> None:
        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE usuarios
                SET senha_hash = ?, troca_senha_obrigatoria = 0,
                    senha_alterada_em = CURRENT_TIMESTAMP, tentativas_falhas = 0,
                    bloqueado_ate = NULL, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (password_hash, user_id),
            )

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
            must_change_password=bool(row["troca_senha_obrigatoria"]),
            failed_login_attempts=int(row["tentativas_falhas"] or 0),
            locked_until=(
                datetime.fromisoformat(row["bloqueado_ate"])
                if row["bloqueado_ate"]
                else None
            ),
            password_changed_at=(
                datetime.fromisoformat(row["senha_alterada_em"])
                if row["senha_alterada_em"]
                else None
            ),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
