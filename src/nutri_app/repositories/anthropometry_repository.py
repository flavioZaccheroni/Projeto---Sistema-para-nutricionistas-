from __future__ import annotations

from datetime import date, datetime

from nutri_app.domain.anthropometry import Anthropometry
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class AnthropometryRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def add(self, anthropometry: Anthropometry) -> int:
        with self.connection_factory.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO antropometrias (
                    paciente_id, consulta_id, data_avaliacao, peso_kg, altura_m, imc,
                    classificacao_imc, circunferencia_cintura_cm,
                    circunferencia_quadril_cm, rcq, rcest, observacoes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._values(anthropometry),
            )
            return int(cursor.lastrowid)

    def update(self, anthropometry: Anthropometry) -> None:
        if anthropometry.id is None:
            raise ValueError("Antropometria sem ID nao pode ser atualizada.")

        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE antropometrias
                SET paciente_id = ?,
                    consulta_id = ?,
                    data_avaliacao = ?,
                    peso_kg = ?,
                    altura_m = ?,
                    imc = ?,
                    classificacao_imc = ?,
                    circunferencia_cintura_cm = ?,
                    circunferencia_quadril_cm = ?,
                    rcq = ?,
                    rcest = ?,
                    observacoes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (*self._values(anthropometry), anthropometry.id),
            )

    def soft_delete(self, anthropometry_id: int) -> None:
        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE antropometrias
                SET deleted_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (anthropometry_id,),
            )

    def get(self, anthropometry_id: int) -> Anthropometry | None:
        with self.connection_factory.connect() as connection:
            row = connection.execute(
                f"{self._select_sql()} WHERE a.id = ? AND a.deleted_at IS NULL AND p.deleted_at IS NULL",
                (anthropometry_id,),
            ).fetchone()
        return self._row_to_anthropometry(row) if row is not None else None

    def list_active(self, patient_query: str = "") -> list[Anthropometry]:
        normalized = f"%{patient_query.strip().lower()}%"
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                f"""
                {self._select_sql()}
                WHERE a.deleted_at IS NULL
                  AND p.deleted_at IS NULL
                  AND (? = '%%' OR lower(p.nome) LIKE ?)
                ORDER BY a.data_avaliacao DESC, a.updated_at DESC
                """,
                (normalized, normalized),
            ).fetchall()
        return [self._row_to_anthropometry(row) for row in rows]

    def _values(self, anthropometry: Anthropometry) -> tuple:
        return (
            anthropometry.patient_id,
            anthropometry.appointment_id,
            anthropometry.assessment_date.isoformat(),
            anthropometry.weight_kg,
            anthropometry.height_m,
            anthropometry.bmi,
            anthropometry.bmi_classification,
            anthropometry.waist_cm,
            anthropometry.hip_cm,
            anthropometry.waist_hip_ratio,
            anthropometry.waist_height_ratio,
            anthropometry.notes,
        )

    def _select_sql(self) -> str:
        return """
            SELECT a.id, a.paciente_id, p.nome AS paciente_nome, a.consulta_id,
                   CASE
                       WHEN c.id IS NULL THEN ''
                       ELSE c.data_hora || ' - ' || c.tipo
                   END AS consulta_rotulo,
                   a.data_avaliacao, a.peso_kg, a.altura_m, a.imc, a.classificacao_imc,
                   a.circunferencia_cintura_cm, a.circunferencia_quadril_cm,
                   a.rcq, a.rcest, a.observacoes, a.created_at, a.updated_at
            FROM antropometrias a
            JOIN pacientes p ON p.id = a.paciente_id
            LEFT JOIN consultas c ON c.id = a.consulta_id AND c.deleted_at IS NULL
        """

    def _row_to_anthropometry(self, row) -> Anthropometry:
        return Anthropometry(
            id=row["id"],
            patient_id=row["paciente_id"],
            patient_name=row["paciente_nome"],
            appointment_id=row["consulta_id"],
            appointment_label=row["consulta_rotulo"] or "",
            assessment_date=date.fromisoformat(row["data_avaliacao"]),
            weight_kg=float(row["peso_kg"]),
            height_m=float(row["altura_m"]),
            bmi=float(row["imc"]),
            bmi_classification=row["classificacao_imc"],
            waist_cm=float(row["circunferencia_cintura_cm"])
            if row["circunferencia_cintura_cm"] is not None
            else None,
            hip_cm=float(row["circunferencia_quadril_cm"])
            if row["circunferencia_quadril_cm"] is not None
            else None,
            waist_hip_ratio=float(row["rcq"]) if row["rcq"] is not None else None,
            waist_height_ratio=float(row["rcest"]) if row["rcest"] is not None else None,
            notes=row["observacoes"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
