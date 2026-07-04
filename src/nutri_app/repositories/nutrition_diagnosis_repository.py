from __future__ import annotations

from datetime import date, datetime

from nutri_app.domain.nutrition_diagnosis import (
    DiagnosisProtocol,
    DiagnosisSeverity,
    NutritionDiagnosis,
)
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class NutritionDiagnosisRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def add(self, diagnosis: NutritionDiagnosis) -> int:
        with self.connection_factory.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO diagnosticos_nutricionais (
                    paciente_id, consulta_id, data_diagnostico, protocolo, criterios,
                    classificacao, gravidade, confirmado, conduta, observacoes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._values(diagnosis),
            )
            return int(cursor.lastrowid)

    def update(self, diagnosis: NutritionDiagnosis) -> None:
        if diagnosis.id is None:
            raise ValueError("Diagnostico nutricional sem ID nao pode ser atualizado.")

        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE diagnosticos_nutricionais
                SET paciente_id = ?,
                    consulta_id = ?,
                    data_diagnostico = ?,
                    protocolo = ?,
                    criterios = ?,
                    classificacao = ?,
                    gravidade = ?,
                    confirmado = ?,
                    conduta = ?,
                    observacoes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (*self._values(diagnosis), diagnosis.id),
            )

    def soft_delete(self, diagnosis_id: int) -> None:
        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE diagnosticos_nutricionais
                SET deleted_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (diagnosis_id,),
            )

    def get(self, diagnosis_id: int) -> NutritionDiagnosis | None:
        with self.connection_factory.connect() as connection:
            row = connection.execute(
                f"""
                {self._select_sql()}
                WHERE d.id = ? AND d.deleted_at IS NULL AND p.deleted_at IS NULL
                """,
                (diagnosis_id,),
            ).fetchone()
        return self._row_to_diagnosis(row) if row is not None else None

    def list_active(self, patient_query: str = "") -> list[NutritionDiagnosis]:
        normalized = f"%{patient_query.strip().lower()}%"
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                f"""
                {self._select_sql()}
                WHERE d.deleted_at IS NULL
                  AND p.deleted_at IS NULL
                  AND (? = '%%' OR lower(p.nome) LIKE ?)
                ORDER BY d.data_diagnostico DESC, d.updated_at DESC
                """,
                (normalized, normalized),
            ).fetchall()
        return [self._row_to_diagnosis(row) for row in rows]

    def _values(self, diagnosis: NutritionDiagnosis) -> tuple:
        return (
            diagnosis.patient_id,
            diagnosis.appointment_id,
            diagnosis.diagnosis_date.isoformat(),
            diagnosis.protocol.value,
            diagnosis.criteria,
            diagnosis.classification,
            diagnosis.severity.value,
            1 if diagnosis.confirmed else 0,
            diagnosis.conduct,
            diagnosis.notes,
        )

    def _select_sql(self) -> str:
        return """
            SELECT d.id, d.paciente_id, p.nome AS paciente_nome, d.consulta_id,
                   CASE
                       WHEN c.id IS NULL THEN ''
                       ELSE c.data_hora || ' - ' || c.tipo
                   END AS consulta_rotulo,
                   d.data_diagnostico, d.protocolo, d.criterios, d.classificacao,
                   d.gravidade, d.confirmado, d.conduta, d.observacoes,
                   d.created_at, d.updated_at
            FROM diagnosticos_nutricionais d
            JOIN pacientes p ON p.id = d.paciente_id
            LEFT JOIN consultas c ON c.id = d.consulta_id AND c.deleted_at IS NULL
        """

    def _row_to_diagnosis(self, row) -> NutritionDiagnosis:
        return NutritionDiagnosis(
            id=row["id"],
            patient_id=row["paciente_id"],
            patient_name=row["paciente_nome"],
            appointment_id=row["consulta_id"],
            appointment_label=row["consulta_rotulo"] or "",
            diagnosis_date=date.fromisoformat(row["data_diagnostico"]),
            protocol=DiagnosisProtocol(row["protocolo"]),
            criteria=row["criterios"],
            classification=row["classificacao"],
            severity=DiagnosisSeverity(row["gravidade"]),
            confirmed=bool(row["confirmado"]),
            conduct=row["conduta"] or "",
            notes=row["observacoes"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
