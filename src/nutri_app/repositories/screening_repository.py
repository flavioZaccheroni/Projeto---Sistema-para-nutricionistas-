from __future__ import annotations

from datetime import datetime

from nutri_app.domain.screening import Screening, ScreeningProtocol
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class ScreeningRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def add(self, screening: Screening) -> int:
        with self.connection_factory.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO triagens (
                    paciente_id, consulta_id, protocolo, pontuacao, classificacao, observacoes
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                self._values(screening),
            )
            return int(cursor.lastrowid)

    def update(self, screening: Screening) -> None:
        if screening.id is None:
            raise ValueError("Triagem sem ID nao pode ser atualizada.")

        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE triagens
                SET paciente_id = ?,
                    consulta_id = ?,
                    protocolo = ?,
                    pontuacao = ?,
                    classificacao = ?,
                    observacoes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (*self._values(screening), screening.id),
            )

    def soft_delete(self, screening_id: int) -> None:
        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE triagens
                SET deleted_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (screening_id,),
            )

    def get(self, screening_id: int) -> Screening | None:
        with self.connection_factory.connect() as connection:
            row = connection.execute(
                f"{self._select_sql()} WHERE t.id = ? AND t.deleted_at IS NULL AND p.deleted_at IS NULL",
                (screening_id,),
            ).fetchone()
        return self._row_to_screening(row) if row is not None else None

    def list_active(self, patient_query: str = "") -> list[Screening]:
        normalized = f"%{patient_query.strip().lower()}%"
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                f"""
                {self._select_sql()}
                WHERE t.deleted_at IS NULL
                  AND p.deleted_at IS NULL
                  AND (? = '%%' OR lower(p.nome) LIKE ?)
                ORDER BY t.updated_at DESC, t.created_at DESC
                """,
                (normalized, normalized),
            ).fetchall()
        return [self._row_to_screening(row) for row in rows]

    def _values(self, screening: Screening) -> tuple:
        return (
            screening.patient_id,
            screening.appointment_id,
            screening.protocol.value,
            screening.score,
            screening.classification,
            screening.notes,
        )

    def _select_sql(self) -> str:
        return """
            SELECT t.id, t.paciente_id, p.nome AS paciente_nome, t.consulta_id,
                   CASE
                       WHEN c.id IS NULL THEN ''
                       ELSE c.data_hora || ' - ' || c.tipo
                   END AS consulta_rotulo,
                   t.protocolo, t.pontuacao, t.classificacao, t.observacoes,
                   t.created_at, t.updated_at
            FROM triagens t
            JOIN pacientes p ON p.id = t.paciente_id
            LEFT JOIN consultas c ON c.id = t.consulta_id AND c.deleted_at IS NULL
        """

    def _row_to_screening(self, row) -> Screening:
        return Screening(
            id=row["id"],
            patient_id=row["paciente_id"],
            patient_name=row["paciente_nome"],
            appointment_id=row["consulta_id"],
            appointment_label=row["consulta_rotulo"] or "",
            protocol=ScreeningProtocol(row["protocolo"]),
            score=float(row["pontuacao"] or 0),
            classification=row["classificacao"],
            notes=row["observacoes"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
