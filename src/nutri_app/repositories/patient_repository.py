from __future__ import annotations

from datetime import date, datetime

from nutri_app.domain.patient import Patient
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.patient_identity import (
    is_valid_cns,
    is_valid_cpf,
    normalize_cns,
    normalize_cpf,
)


class PatientRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def add(self, patient: Patient) -> int:
        with self.connection_factory.connect() as connection:
            cpf, cns, record_number = self._validated_identity(connection, patient)
            cursor = connection.execute(
                """
                INSERT INTO pacientes (
                    nome, data_nascimento, sexo_biologico, telefone, email, convenio, documento,
                    responsavel, observacoes_clinicas, numero_prontuario, cns
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    patient.name,
                    patient.birth_date.isoformat(),
                    patient.biological_sex,
                    patient.phone,
                    patient.email,
                    patient.health_insurance,
                    cpf,
                    patient.responsible,
                    patient.clinical_notes,
                    record_number or None,
                    cns or None,
                ),
            )
            patient_id = int(cursor.lastrowid)
            if not record_number:
                record_number = f"NCP-{patient_id:06d}"
                connection.execute(
                    "UPDATE pacientes SET numero_prontuario = ? WHERE id = ?",
                    (record_number, patient_id),
                )
            return patient_id

    def update(self, patient: Patient) -> None:
        if patient.id is None:
            raise ValueError("Paciente sem ID nao pode ser atualizado.")

        with self.connection_factory.connect() as connection:
            cpf, cns, record_number = self._validated_identity(
                connection,
                patient,
                exclude_patient_id=patient.id,
            )
            if not record_number:
                current = connection.execute(
                    "SELECT numero_prontuario FROM pacientes WHERE id = ?",
                    (patient.id,),
                ).fetchone()
                record_number = (
                    current["numero_prontuario"] if current and current["numero_prontuario"] else ""
                )
            connection.execute(
                """
                UPDATE pacientes
                SET nome = ?,
                    data_nascimento = ?,
                    sexo_biologico = ?,
                    telefone = ?,
                    email = ?,
                    convenio = ?,
                    documento = ?,
                    responsavel = ?,
                    observacoes_clinicas = ?,
                    numero_prontuario = ?,
                    cns = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (
                    patient.name,
                    patient.birth_date.isoformat(),
                    patient.biological_sex,
                    patient.phone,
                    patient.email,
                    patient.health_insurance,
                    cpf,
                    patient.responsible,
                    patient.clinical_notes,
                    record_number or None,
                    cns or None,
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
                SELECT id, nome, data_nascimento, sexo_biologico, telefone, email, convenio,
                       documento, responsavel, observacoes_clinicas, numero_prontuario, cns,
                       created_at, updated_at
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
                SELECT id, nome, data_nascimento, sexo_biologico, telefone, email, convenio,
                       documento, responsavel, numero_prontuario, cns,
                       observacoes_clinicas, created_at, updated_at
                FROM pacientes
                WHERE deleted_at IS NULL
                  AND (
                    ? = '%%'
                    OR lower(nome) LIKE ?
                    OR lower(coalesce(telefone, '')) LIKE ?
                    OR lower(coalesce(email, '')) LIKE ?
                    OR lower(coalesce(documento, '')) LIKE ?
                    OR lower(coalesce(numero_prontuario, '')) LIKE ?
                    OR lower(coalesce(cns, '')) LIKE ?
                  )
                ORDER BY nome
                """,
                (
                    normalized,
                    normalized,
                    normalized,
                    normalized,
                    normalized,
                    normalized,
                    normalized,
                ),
            ).fetchall()

        return [self._row_to_patient(row) for row in rows]

    def _row_to_patient(self, row) -> Patient:
        return Patient(
            id=row["id"],
            name=row["nome"],
            birth_date=date.fromisoformat(row["data_nascimento"]),
            biological_sex=row["sexo_biologico"] or "Feminino",
            phone=row["telefone"] or "",
            email=row["email"] or "",
            health_insurance=row["convenio"] or "",
            document=row["documento"] or "",
            responsible=row["responsavel"] or "",
            clinical_notes=row["observacoes_clinicas"] or "",
            medical_record_number=row["numero_prontuario"] or "",
            cns=row["cns"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _validated_identity(
        self,
        connection,
        patient: Patient,
        exclude_patient_id: int | None = None,
    ) -> tuple[str, str, str]:
        cpf = normalize_cpf(patient.document)
        cns = normalize_cns(patient.cns)
        record_number = patient.medical_record_number.strip().upper()

        if (
            cpf
            and self._policy_enabled(connection, "paciente_validar_cpf")
            and not is_valid_cpf(cpf)
        ):
            raise ValueError("CPF invalido.")
        if (
            cns
            and self._policy_enabled(connection, "paciente_validar_cns")
            and not is_valid_cns(cns)
        ):
            raise ValueError("CNS invalido.")

        if cpf and self._policy_enabled(connection, "paciente_unicidade_cpf"):
            self._ensure_unique(connection, "documento", cpf, "CPF", exclude_patient_id)
        if cns and self._policy_enabled(connection, "paciente_unicidade_cns"):
            self._ensure_unique(connection, "cns", cns, "CNS", exclude_patient_id)
        if record_number and self._policy_enabled(connection, "paciente_unicidade_prontuario"):
            self._ensure_unique(
                connection,
                "numero_prontuario",
                record_number,
                "Numero de prontuario",
                exclude_patient_id,
            )
        return cpf, cns, record_number

    def _policy_enabled(self, connection, key: str) -> bool:
        row = connection.execute(
            "SELECT valor FROM configuracoes WHERE chave = ?",
            (key,),
        ).fetchone()
        return row is None or str(row["valor"]).strip().lower() in {"1", "true", "sim", "yes"}

    def _ensure_unique(
        self,
        connection,
        column: str,
        value: str,
        label: str,
        exclude_patient_id: int | None,
    ) -> None:
        rows = connection.execute(
            f"SELECT id, {column} AS value FROM pacientes WHERE deleted_at IS NULL"
        ).fetchall()
        normalized_value = value.casefold()
        for row in rows:
            if exclude_patient_id is not None and row["id"] == exclude_patient_id:
                continue
            current = row["value"] or ""
            if column in {"documento", "cns"}:
                current = "".join(character for character in current if character.isdigit())
            else:
                current = current.strip().upper()
            if current.casefold() == normalized_value:
                raise ValueError(f"{label} ja cadastrado para outro paciente ativo.")
