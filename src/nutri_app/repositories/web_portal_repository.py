from __future__ import annotations

from datetime import datetime

from nutri_app.domain.web_portal import (
    WebPortalCard,
    WebPortalItem,
    WebPortalPublishRecord,
    WebPortalSnapshot,
)
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class WebPortalRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def build_snapshot(self) -> WebPortalSnapshot:
        with self.connection_factory.connect() as connection:
            active_patients = self._count(
                connection,
                "SELECT COUNT(*) AS total FROM pacientes WHERE deleted_at IS NULL",
            )
            published_content = self._count(
                connection,
                """
                SELECT COUNT(*) AS total
                FROM paciente_app_publicacoes
                WHERE status = 'Publicado' AND deleted_at IS NULL
                """,
            )
            open_finance = self._sum(
                connection,
                """
                SELECT SUM(valor) AS total
                FROM financeiro_lancamentos
                WHERE status IN ('Aberto', 'Vencido') AND deleted_at IS NULL
                """,
            )
            recent_publications = connection.execute(
                """
                SELECT p.nome AS paciente, pub.titulo, pub.tipo, pub.data_publicacao
                FROM paciente_app_publicacoes pub
                JOIN pacientes p ON p.id = pub.paciente_id
                WHERE pub.deleted_at IS NULL AND p.deleted_at IS NULL
                ORDER BY pub.data_publicacao DESC, pub.updated_at DESC
                LIMIT 8
                """
            ).fetchall()
            appointments = connection.execute(
                """
                SELECT p.nome AS paciente, c.data_hora, c.tipo, c.status
                FROM consultas c
                JOIN pacientes p ON p.id = c.paciente_id
                WHERE c.deleted_at IS NULL
                  AND p.deleted_at IS NULL
                  AND lower(c.status) IN ('pendente', 'agendada', 'confirmada')
                ORDER BY c.data_hora
                LIMIT 8
                """
            ).fetchall()

        return WebPortalSnapshot(
            cards=[
                WebPortalCard("Pacientes ativos", str(active_patients), "Base clinica"),
                WebPortalCard("Conteudos publicados", str(published_content), "App paciente"),
                WebPortalCard("Financeiro em aberto", f"R$ {open_finance:.2f}", "Aberto/vencido"),
            ],
            publications=[
                WebPortalItem(
                    title=row["titulo"],
                    description=f"{row['paciente']} - {row['tipo']}",
                    meta=row["data_publicacao"],
                )
                for row in recent_publications
            ],
            appointments=[
                WebPortalItem(
                    title=row["paciente"],
                    description=f"{row['data_hora']} - {row['tipo']}",
                    meta=row["status"],
                )
                for row in appointments
            ],
            generated_at=datetime.now(),
        )

    def add_publish_record(self, record: WebPortalPublishRecord) -> int:
        with self.connection_factory.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO portal_web_publicacoes (
                    titulo, caminho_saida, status, total_paginas, observacoes
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    record.title,
                    record.output_path,
                    record.status,
                    record.total_pages,
                    record.notes,
                ),
            )
            return int(cursor.lastrowid)

    def list_publish_records(self) -> list[WebPortalPublishRecord]:
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, titulo, caminho_saida, status, total_paginas,
                       observacoes, created_at, updated_at
                FROM portal_web_publicacoes
                WHERE deleted_at IS NULL
                ORDER BY created_at DESC, id DESC
                """
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def _count(self, connection, sql: str) -> int:
        row = connection.execute(sql).fetchone()
        return int(row["total"] or 0)

    def _sum(self, connection, sql: str) -> float:
        row = connection.execute(sql).fetchone()
        return float(row["total"] or 0)

    def _row_to_record(self, row) -> WebPortalPublishRecord:
        return WebPortalPublishRecord(
            id=row["id"],
            title=row["titulo"],
            output_path=row["caminho_saida"],
            status=row["status"],
            total_pages=int(row["total_paginas"]),
            notes=row["observacoes"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
