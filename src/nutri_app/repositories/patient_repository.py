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
                    nome, data_nascimento, telefone, email, observacoes_clinicas
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    patient.name,
                    patient.birth_date.isoformat(),
                    patient.phone,
                    patient.email,
                    patient.clinical_notes,
                ),
            )
            return int(cursor.lastrowid)

    def list_active(self) -> list[Patient]:
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, nome, data_nascimento, telefone, email,
                       observacoes_clinicas, created_at, updated_at
                FROM pacientes
                WHERE deleted_at IS NULL
                ORDER BY nome
                """
            ).fetchall()

        return [
            Patient(
                id=row["id"],
                name=row["nome"],
                birth_date=date.fromisoformat(row["data_nascimento"]),
                phone=row["telefone"] or "",
                email=row["email"] or "",
                clinical_notes=row["observacoes_clinicas"] or "",
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
            for row in rows
        ]
