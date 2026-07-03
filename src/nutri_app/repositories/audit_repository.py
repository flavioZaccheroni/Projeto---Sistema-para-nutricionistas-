from __future__ import annotations

from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class AuditRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def log(
        self,
        user_id: int | None,
        action: str,
        entity: str,
        entity_id: int | None,
        details: str = "",
    ) -> None:
        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                INSERT INTO logs_auditoria (usuario_id, acao, entidade, entidade_id, detalhes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, action, entity, entity_id, details),
            )
