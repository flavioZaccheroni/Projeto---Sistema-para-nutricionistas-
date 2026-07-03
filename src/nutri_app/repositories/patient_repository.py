from __future__ import annotations

from datetime import date, datetime

from nutri_app.domain.patient import Patient
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class PatientRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def add(self, patient: Patient) -> int:
        with self.connection_factory.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO pacientes (
                    nome, data_nascimento, telefone, email, convenio, documento,
                    responsavel, observacoes_clinicas
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    patient.name,
                    patient.birth_date.isoformat(),
                    patient.phone,
                    patient.email,
                    patient.health_insurance,
                    patient.document,
                    patient.responsible,
                    patient.clinical_notes,
                ),
            )
            return int(cursor.lastrowid)

    def update(self, patient: Patient) -> None:
        if patient.id is None:
            raise ValueError("Paciente sem ID nao pode ser atualizado.")

        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE pacientes
                SET nome = ?,
                    data_nascimento = ?,
                    telefone = ?,
                    email = ?,
                    convenio = ?,
                    documento = ?,
                    responsavel = ?,
                    observacoes_clinicas = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (
                    patient.name,
                    patient.birth_date.isoformat(),
                    patient.phone,
                    patient.email,
                    patient.health_insurance,
                    patient.document,
                    patient.responsible,
                    patient.clinical_notes,
                    patient.id,
                ),
            )

    def soft_delete(self, patient_id: int) -> None:
        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE pacientes
                SET deleted_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (patient_id,),
            )

    def get(self, patient_id: int) -> Patient | None:
        with self.connection_factory.connect() as connection:
            row = connection.execute(
                """
                SELECT id, nome, data_nascimento, telefone, email, convenio,
                       documento, responsavel, observacoes_clinicas, created_at, updated_at
                FROM pacientes
                WHERE id = ? AND deleted_at IS NULL
                """,
                (patient_id,),
            ).fetchone()

        return self._row_to_patient(row) if row is not None else None

    def list_active(self) -> list[Patient]:
        return self.search("")

    def search(self, query: str) -> list[Patient]:
        normalized = f"%{query.strip().lower()}%"
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, nome, data_nascimento, telefone, email, convenio,
                       documento, responsavel,
                       observacoes_clinicas, created_at, updated_at
                FROM pacientes
                WHERE deleted_at IS NULL
                  AND (
                    ? = '%%'
                    OR lower(nome) LIKE ?
                    OR lower(coalesce(telefone, '')) LIKE ?
                    OR lower(coalesce(email, '')) LIKE ?
                    OR lower(coalesce(documento, '')) LIKE ?
                  )
                ORDER BY nome
                """,
                (normalized, normalized, normalized, normalized, normalized),
            ).fetchall()

        return [self._row_to_patient(row) for row in rows]

    def _row_to_patient(self, row) -> Patient:
        return Patient(
            id=row["id"],
            name=row["nome"],
            birth_date=date.fromisoformat(row["data_nascimento"]),
            phone=row["telefone"] or "",
            email=row["email"] or "",
            health_insurance=row["convenio"] or "",
            document=row["documento"] or "",
            responsible=row["responsavel"] or "",
            clinical_notes=row["observacoes_clinicas"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
