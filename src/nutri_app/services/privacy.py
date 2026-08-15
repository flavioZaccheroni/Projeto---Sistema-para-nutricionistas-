from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


@dataclass(frozen=True)
class PrivacyExportResult:
    patient_id: int
    file_path: Path
    tables_exported: int
    records_exported: int


class PatientPrivacyService:
    """LGPD operations that preserve traceability and avoid silent clinical deletion."""

    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def record_consent(
        self,
        patient_id: int,
        policy_version: str,
        granted: bool,
        user_id: int,
        notes: str = "",
    ) -> int:
        if not policy_version.strip():
            raise ValueError("A versao da politica de privacidade e obrigatoria.")
        with self.connection_factory.connect() as connection:
            if not self._patient_exists(connection, patient_id):
                raise ValueError("Paciente nao encontrado.")
            if not granted:
                connection.execute(
                    """
                    UPDATE consentimentos_privacidade
                    SET revogado_em = CURRENT_TIMESTAMP
                    WHERE paciente_id = ? AND revogado_em IS NULL
                    """,
                    (patient_id,),
                )
            cursor = connection.execute(
                """
                INSERT INTO consentimentos_privacidade (
                    paciente_id, versao_politica, concedido, registrado_por, observacoes
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (patient_id, policy_version.strip(), 1 if granted else 0, user_id, notes),
            )
            if granted:
                connection.execute(
                    """
                    UPDATE pacientes
                    SET consentimento_lgpd_em = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (patient_id,),
                )
            return int(cursor.lastrowid)

    def has_active_consent(self, patient_id: int) -> bool:
        with self.connection_factory.connect() as connection:
            row = connection.execute(
                """
                SELECT concedido, revogado_em
                FROM consentimentos_privacidade
                WHERE paciente_id = ?
                ORDER BY registrado_em DESC, id DESC
                LIMIT 1
                """,
                (patient_id,),
            ).fetchone()
        return bool(row and row["concedido"] and not row["revogado_em"])

    def export_patient_data(self, patient_id: int, output_dir: Path) -> PrivacyExportResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        with self.connection_factory.connect() as connection:
            if not self._patient_exists(connection, patient_id):
                raise ValueError("Paciente nao encontrado.")
            exported = self._collect_related_records(connection, patient_id)
            request = connection.execute(
                """
                INSERT INTO solicitacoes_privacidade (paciente_id, tipo, status)
                VALUES (?, 'Exportacao', 'Em processamento')
                """,
                (patient_id,),
            )
            request_id = int(request.lastrowid)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = output_dir / f"dados_paciente_{patient_id}_{timestamp}.json"
        payload = {
            "metadata": {
                "patient_id": patient_id,
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "purpose": "Portabilidade/acesso do titular (LGPD)",
                "format_version": "1.0",
            },
            "data": exported,
        }
        file_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        records = sum(len(rows) for rows in exported.values())
        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE solicitacoes_privacidade
                SET status = 'Concluida', caminho_exportacao = ?,
                    concluida_em = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (str(file_path), request_id),
            )
        return PrivacyExportResult(patient_id, file_path, len(exported), records)

    def anonymize_patient(self, patient_id: int, reason: str, today: date | None = None) -> None:
        if len(reason.strip()) < 10:
            raise ValueError("Informe uma justificativa com pelo menos 10 caracteres.")
        reference_date = today or date.today()
        with self.connection_factory.connect() as connection:
            row = connection.execute(
                "SELECT retencao_ate, anonimizado_em FROM pacientes WHERE id = ?",
                (patient_id,),
            ).fetchone()
            if row is None:
                raise ValueError("Paciente nao encontrado.")
            if row["anonimizado_em"]:
                raise ValueError("Paciente ja foi anonimizado.")
            if row["retencao_ate"] and date.fromisoformat(row["retencao_ate"]) > reference_date:
                raise ValueError("O prazo de retencao do prontuario ainda nao terminou.")
            alias = f"Paciente anonimizado {patient_id}"
            connection.execute(
                """
                UPDATE pacientes
                SET nome = ?, telefone = '', email = '', convenio = '', documento = '', cns = '',
                    numero_prontuario = '',
                    responsavel = '', observacoes_clinicas = '', anonimizado_em = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (alias, patient_id),
            )
            connection.execute(
                """
                INSERT INTO solicitacoes_privacidade (
                    paciente_id, tipo, status, justificativa, concluida_em
                ) VALUES (?, 'Anonimizacao', 'Concluida', ?, CURRENT_TIMESTAMP)
                """,
                (patient_id, reason.strip()),
            )

    def _collect_related_records(self, connection, patient_id: int) -> dict[str, list[dict]]:
        tables = [
            row["name"]
            for row in connection.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            ).fetchall()
        ]
        result: dict[str, list[dict]] = {}
        known_ids: dict[str, set[int]] = {"pacientes": {patient_id}}
        patient = connection.execute(
            "SELECT * FROM pacientes WHERE id = ?", (patient_id,)
        ).fetchall()
        result["pacientes"] = [dict(row) for row in patient]

        changed = True
        while changed:
            changed = False
            for table in tables:
                if table in result or table in {"schema_migrations"}:
                    continue
                foreign_keys = connection.execute(f'PRAGMA foreign_key_list("{table}")').fetchall()
                clauses: list[str] = []
                params: list[object] = []
                for foreign_key in foreign_keys:
                    parent = foreign_key["table"]
                    parent_ids = known_ids.get(parent)
                    if not parent_ids or foreign_key["to"] != "id":
                        continue
                    placeholders = ",".join("?" for _ in parent_ids)
                    clauses.append(f'"{foreign_key["from"]}" IN ({placeholders})')
                    params.extend(sorted(parent_ids))
                if not clauses:
                    continue
                rows = connection.execute(
                    f'SELECT * FROM "{table}" WHERE ' + " OR ".join(clauses),
                    params,
                ).fetchall()
                result[table] = [dict(row) for row in rows]
                ids = {int(row["id"]) for row in rows if "id" in row.keys()}
                if ids:
                    known_ids[table] = ids
                changed = True
        return result

    def _patient_exists(self, connection, patient_id: int) -> bool:
        row = connection.execute("SELECT 1 FROM pacientes WHERE id = ?", (patient_id,)).fetchone()
        return row is not None
