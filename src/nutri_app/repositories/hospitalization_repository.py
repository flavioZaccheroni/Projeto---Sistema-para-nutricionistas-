from __future__ import annotations

from datetime import date, datetime

from nutri_app.domain.hospitalization import Hospitalization
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class HospitalizationRepository:
    VALID_STATUSES = {"Ativa", "Alta", "Transferida", "Cancelada"}

    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def add(self, hospitalization: Hospitalization) -> int:
        self._validate(hospitalization)
        with self.connection_factory.connect() as connection:
            patient = connection.execute(
                "SELECT 1 FROM pacientes WHERE id = ? AND deleted_at IS NULL",
                (hospitalization.patient_id,),
            ).fetchone()
            if patient is None:
                raise ValueError("Paciente nao encontrado.")
            cursor = connection.execute(
                """
                INSERT INTO internacoes (
                    paciente_id, data_admissao, data_alta, unidade, ala, leito, convenio,
                    equipe_responsavel, diagnosticos, condicao_alta, status, observacoes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._values(hospitalization),
            )
            return int(cursor.lastrowid)

    def update(self, hospitalization: Hospitalization) -> None:
        if hospitalization.id is None:
            raise ValueError("Internacao sem ID nao pode ser atualizada.")
        self._validate(hospitalization)
        with self.connection_factory.connect() as connection:
            cursor = connection.execute(
                """
                UPDATE internacoes
                SET data_admissao = ?, data_alta = ?, unidade = ?, ala = ?, leito = ?,
                    convenio = ?, equipe_responsavel = ?, diagnosticos = ?,
                    condicao_alta = ?, status = ?, observacoes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND paciente_id = ? AND deleted_at IS NULL
                """,
                (
                    hospitalization.admission_date.isoformat(),
                    hospitalization.discharge_date.isoformat()
                    if hospitalization.discharge_date
                    else None,
                    hospitalization.unit.strip(),
                    hospitalization.ward.strip(),
                    hospitalization.bed.strip(),
                    hospitalization.health_insurance.strip(),
                    hospitalization.responsible_team.strip(),
                    hospitalization.diagnoses.strip(),
                    hospitalization.discharge_condition.strip(),
                    hospitalization.status,
                    hospitalization.notes.strip(),
                    hospitalization.id,
                    hospitalization.patient_id,
                ),
            )
            if cursor.rowcount == 0:
                raise ValueError("Internacao nao encontrada.")

    def get(self, hospitalization_id: int) -> Hospitalization | None:
        with self.connection_factory.connect() as connection:
            row = connection.execute(
                "SELECT * FROM internacoes WHERE id = ? AND deleted_at IS NULL",
                (hospitalization_id,),
            ).fetchone()
        return self._row_to_hospitalization(row) if row else None

    def list_for_patient(self, patient_id: int) -> list[Hospitalization]:
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM internacoes
                WHERE paciente_id = ? AND deleted_at IS NULL
                ORDER BY data_admissao DESC, id DESC
                """,
                (patient_id,),
            ).fetchall()
        return [self._row_to_hospitalization(row) for row in rows]

    def soft_delete(self, hospitalization_id: int, patient_id: int) -> None:
        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE internacoes
                SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND paciente_id = ? AND deleted_at IS NULL
                """,
                (hospitalization_id, patient_id),
            )

    def _validate(self, hospitalization: Hospitalization) -> None:
        if not hospitalization.unit.strip():
            raise ValueError("Unidade de internacao e obrigatoria.")
        if hospitalization.status not in self.VALID_STATUSES:
            raise ValueError("Status de internacao invalido.")
        if (
            hospitalization.discharge_date
            and hospitalization.discharge_date < hospitalization.admission_date
        ):
            raise ValueError("A data de alta nao pode ser anterior a admissao.")
        if hospitalization.status == "Alta" and hospitalization.discharge_date is None:
            raise ValueError("Informe a data de alta para concluir a internacao.")

    def _values(self, hospitalization: Hospitalization) -> tuple[object, ...]:
        return (
            hospitalization.patient_id,
            hospitalization.admission_date.isoformat(),
            hospitalization.discharge_date.isoformat() if hospitalization.discharge_date else None,
            hospitalization.unit.strip(),
            hospitalization.ward.strip(),
            hospitalization.bed.strip(),
            hospitalization.health_insurance.strip(),
            hospitalization.responsible_team.strip(),
            hospitalization.diagnoses.strip(),
            hospitalization.discharge_condition.strip(),
            hospitalization.status,
            hospitalization.notes.strip(),
        )

    def _row_to_hospitalization(self, row) -> Hospitalization:
        return Hospitalization(
            id=row["id"],
            patient_id=row["paciente_id"],
            admission_date=date.fromisoformat(row["data_admissao"]),
            discharge_date=date.fromisoformat(row["data_alta"]) if row["data_alta"] else None,
            unit=row["unidade"],
            ward=row["ala"] or "",
            bed=row["leito"] or "",
            health_insurance=row["convenio"] or "",
            responsible_team=row["equipe_responsavel"] or "",
            diagnoses=row["diagnosticos"] or "",
            discharge_condition=row["condicao_alta"] or "",
            status=row["status"],
            notes=row["observacoes"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
