from __future__ import annotations

from datetime import datetime

from nutri_app.domain.integration import (
    ExternalIntegration,
    IntegrationDirection,
    IntegrationExecution,
    IntegrationStatus,
    IntegrationType,
)
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class IntegrationRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def add_integration(self, integration: ExternalIntegration) -> int:
        with self.connection_factory.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO integracoes_externas (
                    nome, tipo, endpoint, ativo, credencial_alias, observacoes
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    integration.name,
                    integration.integration_type.value,
                    integration.endpoint,
                    1 if integration.active else 0,
                    integration.credential_alias,
                    integration.notes,
                ),
            )
            return int(cursor.lastrowid)

    def list_integrations(self) -> list[ExternalIntegration]:
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, nome, tipo, endpoint, ativo, credencial_alias,
                       observacoes, created_at, updated_at
                FROM integracoes_externas
                WHERE deleted_at IS NULL
                ORDER BY nome
                """
            ).fetchall()
        return [self._row_to_integration(row) for row in rows]

    def get_integration(self, integration_id: int) -> ExternalIntegration | None:
        with self.connection_factory.connect() as connection:
            row = connection.execute(
                """
                SELECT id, nome, tipo, endpoint, ativo, credencial_alias,
                       observacoes, created_at, updated_at
                FROM integracoes_externas
                WHERE id = ? AND deleted_at IS NULL
                """,
                (integration_id,),
            ).fetchone()
        return self._row_to_integration(row) if row is not None else None

    def add_execution(self, execution: IntegrationExecution) -> int:
        with self.connection_factory.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO integracao_execucoes (
                    integracao_id, direcao, entidade, status, payload, resultado
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    execution.integration_id,
                    execution.direction.value,
                    execution.entity,
                    execution.status.value,
                    execution.payload,
                    execution.result,
                ),
            )
            return int(cursor.lastrowid)

    def list_executions(self) -> list[IntegrationExecution]:
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                """
                SELECT ex.id, ex.integracao_id, i.nome AS integracao_nome, ex.direcao,
                       ex.entidade, ex.status, ex.payload, ex.resultado,
                       ex.created_at, ex.updated_at
                FROM integracao_execucoes ex
                LEFT JOIN integracoes_externas i ON i.id = ex.integracao_id
                WHERE ex.deleted_at IS NULL
                ORDER BY ex.created_at DESC, ex.id DESC
                """
            ).fetchall()
        return [self._row_to_execution(row) for row in rows]

    def _row_to_integration(self, row) -> ExternalIntegration:
        return ExternalIntegration(
            id=row["id"],
            name=row["nome"],
            integration_type=IntegrationType(row["tipo"]),
            endpoint=row["endpoint"] or "",
            active=bool(row["ativo"]),
            credential_alias=row["credencial_alias"] or "",
            notes=row["observacoes"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _row_to_execution(self, row) -> IntegrationExecution:
        return IntegrationExecution(
            id=row["id"],
            integration_id=row["integracao_id"],
            integration_name=row["integracao_nome"] or "",
            direction=IntegrationDirection(row["direcao"]),
            entity=row["entidade"],
            status=IntegrationStatus(row["status"]),
            payload=row["payload"] or "",
            result=row["resultado"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
