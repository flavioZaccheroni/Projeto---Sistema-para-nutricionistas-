from __future__ import annotations

from datetime import datetime

from nutri_app.domain.anamnesis import Anamnesis
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class AnamnesisRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def add(self, anamnesis: Anamnesis) -> int:
        with self.connection_factory.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO anamnese (
                    paciente_id, consulta_id, queixa_principal, historia_doenca_atual,
                    historico_patologico, historico_familiar, rotina_alimentar,
                    comportamento_alimentar, sintomas_gastrointestinais, observacoes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._values(anamnesis),
            )
            return int(cursor.lastrowid)

    def update(self, anamnesis: Anamnesis) -> None:
        if anamnesis.id is None:
            raise ValueError("Anamnese sem ID nao pode ser atualizada.")

        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE anamnese
                SET paciente_id = ?,
                    consulta_id = ?,
                    queixa_principal = ?,
                    historia_doenca_atual = ?,
                    historico_patologico = ?,
                    historico_familiar = ?,
                    rotina_alimentar = ?,
                    comportamento_alimentar = ?,
                    sintomas_gastrointestinais = ?,
                    observacoes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (*self._values(anamnesis), anamnesis.id),
            )

    def soft_delete(self, anamnesis_id: int) -> None:
        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE anamnese
                SET deleted_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (anamnesis_id,),
            )

    def get(self, anamnesis_id: int) -> Anamnesis | None:
        with self.connection_factory.connect() as connection:
            row = connection.execute(
                f"{self._select_sql()} WHERE a.id = ? AND a.deleted_at IS NULL AND p.deleted_at IS NULL",
                (anamnesis_id,),
            ).fetchone()
        return self._row_to_anamnesis(row) if row is not None else None

    def list_active(self, patient_query: str = "") -> list[Anamnesis]:
        normalized = f"%{patient_query.strip().lower()}%"
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                f"""
                {self._select_sql()}
                WHERE a.deleted_at IS NULL
                  AND p.deleted_at IS NULL
                  AND (? = '%%' OR lower(p.nome) LIKE ?)
                ORDER BY a.updated_at DESC, a.created_at DESC
                """,
                (normalized, normalized),
            ).fetchall()
        return [self._row_to_anamnesis(row) for row in rows]

    def _values(self, anamnesis: Anamnesis) -> tuple:
        return (
            anamnesis.patient_id,
            anamnesis.appointment_id,
            anamnesis.chief_complaint,
            anamnesis.current_disease_history,
            anamnesis.pathological_history,
            anamnesis.family_history,
            anamnesis.food_routine,
            anamnesis.eating_behavior,
            anamnesis.gastrointestinal_symptoms,
            anamnesis.notes,
        )

    def _select_sql(self) -> str:
        return """
            SELECT a.id, a.paciente_id, p.nome AS paciente_nome, a.consulta_id,
                   CASE
                       WHEN c.id IS NULL THEN ''
                       ELSE c.data_hora || ' - ' || c.tipo
                   END AS consulta_rotulo,
                   a.queixa_principal, a.historia_doenca_atual, a.historico_patologico,
                   a.historico_familiar, a.rotina_alimentar, a.comportamento_alimentar,
                   a.sintomas_gastrointestinais, a.observacoes, a.created_at, a.updated_at
            FROM anamnese a
            JOIN pacientes p ON p.id = a.paciente_id
            LEFT JOIN consultas c ON c.id = a.consulta_id AND c.deleted_at IS NULL
        """

    def _row_to_anamnesis(self, row) -> Anamnesis:
        return Anamnesis(
            id=row["id"],
            patient_id=row["paciente_id"],
            patient_name=row["paciente_nome"],
            appointment_id=row["consulta_id"],
            appointment_label=row["consulta_rotulo"] or "",
            chief_complaint=row["queixa_principal"] or "",
            current_disease_history=row["historia_doenca_atual"] or "",
            pathological_history=row["historico_patologico"] or "",
            family_history=row["historico_familiar"] or "",
            food_routine=row["rotina_alimentar"] or "",
            eating_behavior=row["comportamento_alimentar"] or "",
            gastrointestinal_symptoms=row["sintomas_gastrointestinais"] or "",
            notes=row["observacoes"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
