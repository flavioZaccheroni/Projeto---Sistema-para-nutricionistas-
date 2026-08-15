from __future__ import annotations

import json
from datetime import date, datetime

from nutri_app.domain.supplement_prescription import SupplementFollowUp, SupplementPrescription
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class SupplementPrescriptionRepository:
    STATUSES = {"Ativa", "Concluida", "Suspensa", "Cancelada"}

    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def add(self, prescription: SupplementPrescription) -> int:
        self._validate_prescription(prescription)
        with self.connection_factory.connect() as connection:
            patient = connection.execute(
                "SELECT 1 FROM pacientes WHERE id = ? AND deleted_at IS NULL",
                (prescription.patient_id,),
            ).fetchone()
            supplement = connection.execute(
                "SELECT * FROM suplementos WHERE id = ? AND deleted_at IS NULL",
                (prescription.supplement_id,),
            ).fetchone()
            if patient is None:
                raise ValueError("Paciente nao encontrado.")
            if supplement is None:
                raise ValueError("Suplemento nao encontrado.")
            snapshot = {key: supplement[key] for key in supplement.keys()}
            factor = prescription.quantity / float(supplement["porcao_base"])
            daily_factor = factor * prescription.frequency_per_day
            daily_intake = {
                "energia_kcal": float(supplement["energia_kcal"]) * daily_factor,
                "proteina_g": float(supplement["proteina_g"]) * daily_factor,
                "carboidrato_g": float(supplement["carboidrato_g"]) * daily_factor,
                "lipidios_g": float(supplement["lipidios_g"]) * daily_factor,
                "fibras_g": float(supplement["fibras_g"]) * daily_factor,
                "sodio_mg": float(supplement["sodio_mg"]) * daily_factor,
            }
            cursor = connection.execute(
                """
                INSERT INTO prescricoes_suplementos (
                    paciente_id, suplemento_id, suplemento_snapshot_json, data_inicio,
                    data_fim, quantidade, unidade, frequencia_dia, horarios, objetivo,
                    instrucoes, aporte_diario_json, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    prescription.patient_id,
                    prescription.supplement_id,
                    json.dumps(snapshot, ensure_ascii=False, sort_keys=True),
                    prescription.start_date.isoformat(),
                    prescription.end_date.isoformat(),
                    prescription.quantity,
                    prescription.unit.strip(),
                    prescription.frequency_per_day,
                    prescription.times.strip(),
                    prescription.objective.strip(),
                    prescription.instructions.strip(),
                    json.dumps(daily_intake, ensure_ascii=False, sort_keys=True),
                    prescription.status,
                ),
            )
            return int(cursor.lastrowid)

    def get(self, prescription_id: int) -> SupplementPrescription | None:
        with self.connection_factory.connect() as connection:
            row = connection.execute(
                """
                SELECT ps.*, p.nome AS paciente_nome, s.nome AS suplemento_nome
                FROM prescricoes_suplementos ps
                JOIN pacientes p ON p.id = ps.paciente_id
                LEFT JOIN suplementos s ON s.id = ps.suplemento_id
                WHERE ps.id = ? AND ps.deleted_at IS NULL
                """,
                (prescription_id,),
            ).fetchone()
        return self._row_to_prescription(row) if row else None

    def list_for_patient(self, patient_id: int) -> list[SupplementPrescription]:
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                """
                SELECT ps.*, p.nome AS paciente_nome, s.nome AS suplemento_nome
                FROM prescricoes_suplementos ps
                JOIN pacientes p ON p.id = ps.paciente_id
                LEFT JOIN suplementos s ON s.id = ps.suplemento_id
                WHERE ps.paciente_id = ? AND ps.deleted_at IS NULL
                ORDER BY ps.data_inicio DESC, ps.id DESC
                """,
                (patient_id,),
            ).fetchall()
        return [self._row_to_prescription(row) for row in rows]

    def add_follow_up(self, follow_up: SupplementFollowUp) -> int:
        if not 0 <= follow_up.acceptance <= 10:
            raise ValueError("Aceitacao deve estar entre 0 e 10.")
        if not 0 <= follow_up.adherence_percent <= 100:
            raise ValueError("Adesao deve estar entre 0 e 100%.")
        with self.connection_factory.connect() as connection:
            prescription = connection.execute(
                "SELECT status FROM prescricoes_suplementos WHERE id = ? AND deleted_at IS NULL",
                (follow_up.prescription_id,),
            ).fetchone()
            if prescription is None:
                raise ValueError("Prescricao de suplemento nao encontrada.")
            cursor = connection.execute(
                """
                INSERT INTO acompanhamentos_suplementacao (
                    prescricao_id, data_registro, aceitacao, adesao_percentual,
                    intercorrencias, resposta_clinica, motivo_suspensao
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    follow_up.prescription_id,
                    follow_up.record_date.isoformat(),
                    follow_up.acceptance,
                    follow_up.adherence_percent,
                    follow_up.incidents.strip(),
                    follow_up.clinical_response.strip(),
                    follow_up.suspension_reason.strip(),
                ),
            )
            if follow_up.suspension_reason.strip():
                connection.execute(
                    """
                    UPDATE prescricoes_suplementos
                    SET status = 'Suspensa', updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (follow_up.prescription_id,),
                )
            return int(cursor.lastrowid)

    def list_follow_ups(self, prescription_id: int) -> list[SupplementFollowUp]:
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM acompanhamentos_suplementacao
                WHERE prescricao_id = ?
                ORDER BY data_registro DESC, id DESC
                """,
                (prescription_id,),
            ).fetchall()
        return [
            SupplementFollowUp(
                id=row["id"],
                prescription_id=row["prescricao_id"],
                record_date=date.fromisoformat(row["data_registro"]),
                acceptance=row["aceitacao"],
                adherence_percent=row["adesao_percentual"],
                incidents=row["intercorrencias"] or "",
                clinical_response=row["resposta_clinica"] or "",
                suspension_reason=row["motivo_suspensao"] or "",
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    def _validate_prescription(self, prescription: SupplementPrescription) -> None:
        if prescription.quantity <= 0 or not prescription.unit.strip():
            raise ValueError("Quantidade e unidade da prescricao sao obrigatorias.")
        if prescription.frequency_per_day <= 0:
            raise ValueError("Frequencia diaria deve ser maior que zero.")
        if prescription.end_date < prescription.start_date:
            raise ValueError("Data final nao pode ser anterior a data inicial.")
        if not prescription.times.strip():
            raise ValueError("Informe os horarios da suplementacao.")
        if not prescription.objective.strip() or not prescription.instructions.strip():
            raise ValueError("Objetivo e instrucoes sao obrigatorios.")
        if prescription.status not in self.STATUSES:
            raise ValueError("Status da prescricao invalido.")

    def _row_to_prescription(self, row) -> SupplementPrescription:
        snapshot = json.loads(row["suplemento_snapshot_json"])
        return SupplementPrescription(
            id=row["id"],
            patient_id=row["paciente_id"],
            patient_name=row["paciente_nome"],
            supplement_id=row["suplemento_id"],
            supplement_name=snapshot.get("nome") or row["suplemento_nome"] or "",
            supplement_snapshot=snapshot,
            daily_intake=json.loads(row["aporte_diario_json"]),
            start_date=date.fromisoformat(row["data_inicio"]),
            end_date=date.fromisoformat(row["data_fim"]),
            quantity=row["quantidade"],
            unit=row["unidade"],
            frequency_per_day=row["frequencia_dia"],
            times=row["horarios"],
            objective=row["objetivo"],
            instructions=row["instrucoes"],
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
