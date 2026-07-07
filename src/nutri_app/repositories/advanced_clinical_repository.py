from __future__ import annotations

import json
from datetime import date, datetime

from nutri_app.domain.advanced_clinical import AdvancedClinicalRecord
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class AdvancedClinicalRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def add(self, record: AdvancedClinicalRecord) -> int:
        with self.connection_factory.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO registros_clinicos_avancados (
                    modulo, paciente_id, data_registro, perfil, entradas_json,
                    resultado, observacoes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.module,
                    record.patient_id,
                    record.record_date.isoformat(),
                    record.profile,
                    json.dumps(record.inputs, ensure_ascii=False, sort_keys=True),
                    record.result,
                    record.notes,
                ),
            )
            return int(cursor.lastrowid)

    def list_by_module(self, module: str) -> list[AdvancedClinicalRecord]:
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                """
                SELECT r.id, r.modulo, r.paciente_id, p.nome AS paciente_nome,
                       r.data_registro, r.perfil, r.entradas_json, r.resultado,
                       r.observacoes, r.created_at, r.updated_at
                FROM registros_clinicos_avancados r
                LEFT JOIN pacientes p ON p.id = r.paciente_id
                WHERE r.modulo = ? AND r.deleted_at IS NULL
                ORDER BY r.data_registro DESC, r.id DESC
                """,
                (module,),
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def _row_to_record(self, row) -> AdvancedClinicalRecord:
        return AdvancedClinicalRecord(
            id=row["id"],
            module=row["modulo"],
            patient_id=row["paciente_id"],
            patient_name=row["paciente_nome"] or "",
            record_date=date.fromisoformat(row["data_registro"]),
            profile=row["perfil"],
            inputs=json.loads(row["entradas_json"] or "{}"),
            result=row["resultado"],
            notes=row["observacoes"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
