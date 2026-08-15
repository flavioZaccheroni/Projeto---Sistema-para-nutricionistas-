from __future__ import annotations

from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class ClinicalGovernanceRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def list_references(self) -> list[dict[str, object]]:
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, modulo, regra, versao, fonte, status_validacao,
                       revisado_por, revisado_em, observacoes
                FROM referencias_clinicas
                ORDER BY modulo, regra
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def review(
        self,
        reference_id: int,
        status: str,
        reviewer: str,
        notes: str,
    ) -> None:
        if status not in {"Pendente", "Aprovada", "Reprovada"}:
            raise ValueError("Status de validacao clinica invalido.")
        if status != "Pendente" and len(reviewer.strip()) < 5:
            raise ValueError("Informe o nome e registro do profissional revisor.")
        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE referencias_clinicas
                SET status_validacao = ?, revisado_por = ?,
                    revisado_em = CASE WHEN ? = 'Pendente' THEN NULL ELSE CURRENT_TIMESTAMP END,
                    observacoes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, reviewer.strip(), status, notes.strip(), reference_id),
            )

    def pending_count(self) -> int:
        with self.connection_factory.connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS total FROM referencias_clinicas
                WHERE status_validacao <> 'Aprovada'
                """
            ).fetchone()
        return int(row["total"])
