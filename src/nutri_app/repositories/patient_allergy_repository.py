from __future__ import annotations

from datetime import datetime

from nutri_app.domain.patient_allergy import AllergyCategory, PatientAllergy
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class PatientAllergyRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def add(self, allergy: PatientAllergy) -> int:
        with self.connection_factory.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO paciente_alergias (
                    paciente_id, tipo, alergeno, gravidade, conduta, observacoes
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    allergy.patient_id,
                    allergy.category.value,
                    allergy.allergen,
                    allergy.severity,
                    allergy.conduct,
                    allergy.notes,
                ),
            )
            return int(cursor.lastrowid)

    def list_for_patient(self, patient_id: int) -> list[PatientAllergy]:
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, paciente_id, tipo, alergeno, gravidade, conduta, observacoes,
                       created_at, updated_at
                FROM paciente_alergias
                WHERE paciente_id = ? AND deleted_at IS NULL
                ORDER BY alergeno
                """,
                (patient_id,),
            ).fetchall()
        return [self._row_to_allergy(row) for row in rows]

    def replace_for_patient(self, patient_id: int, allergies: list[PatientAllergy]) -> None:
        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE paciente_alergias
                SET deleted_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE paciente_id = ? AND deleted_at IS NULL
                """,
                (patient_id,),
            )
            for allergy in allergies:
                connection.execute(
                    """
                    INSERT INTO paciente_alergias (
                        paciente_id, tipo, alergeno, gravidade, conduta, observacoes
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        patient_id,
                        allergy.category.value,
                        allergy.allergen,
                        allergy.severity,
                        allergy.conduct,
                        allergy.notes,
                    ),
                )

    def _row_to_allergy(self, row) -> PatientAllergy:
        return PatientAllergy(
            id=row["id"],
            patient_id=row["paciente_id"],
            category=AllergyCategory(row["tipo"]),
            allergen=row["alergeno"],
            severity=row["gravidade"] or "",
            conduct=row["conduta"] or "",
            notes=row["observacoes"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
