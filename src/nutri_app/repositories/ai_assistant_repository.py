from __future__ import annotations

from datetime import datetime

from nutri_app.domain.ai_assistant import AIAssistantExecution, AIAssistantRequestType
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class AIAssistantRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def build_context(self, patient_id: int | None) -> dict[str, object]:
        if patient_id is None:
            return {}
        with self.connection_factory.connect() as connection:
            patient = connection.execute(
                "SELECT nome FROM pacientes WHERE id = ? AND deleted_at IS NULL",
                (patient_id,),
            ).fetchone()
            anthropometry = connection.execute(
                """
                SELECT imc
                FROM antropometrias
                WHERE paciente_id = ? AND deleted_at IS NULL
                ORDER BY data_avaliacao DESC, updated_at DESC
                LIMIT 1
                """,
                (patient_id,),
            ).fetchone()
            diagnosis = connection.execute(
                """
                SELECT classificacao
                FROM diagnosticos_nutricionais
                WHERE paciente_id = ? AND deleted_at IS NULL
                ORDER BY data_diagnostico DESC, updated_at DESC
                LIMIT 1
                """,
                (patient_id,),
            ).fetchone()
            plan = connection.execute(
                """
                SELECT objetivo
                FROM planos_alimentares
                WHERE paciente_id = ? AND deleted_at IS NULL
                ORDER BY data_inicio DESC, updated_at DESC
                LIMIT 1
                """,
                (patient_id,),
            ).fetchone()
            lab_alerts = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM exame_itens item
                JOIN exames_laboratoriais exam ON exam.id = item.exame_id
                WHERE exam.paciente_id = ?
                  AND exam.deleted_at IS NULL
                  AND item.deleted_at IS NULL
                  AND item.alerta IS NOT NULL
                  AND trim(item.alerta) <> ''
                """,
                (patient_id,),
            ).fetchone()
            adherence = connection.execute(
                """
                SELECT AVG(percentual_adesao) AS media
                FROM paciente_app_adesoes
                WHERE paciente_id = ? AND deleted_at IS NULL
                """,
                (patient_id,),
            ).fetchone()
        return {
            "patient_name": patient["nome"] if patient else "",
            "bmi": float(anthropometry["imc"]) if anthropometry else None,
            "diagnosis": diagnosis["classificacao"] if diagnosis else "",
            "meal_plan_objective": plan["objetivo"] if plan else "",
            "lab_alerts": int(lab_alerts["total"] or 0),
            "average_adherence": float(adherence["media"] or 0),
        }

    def add_execution(self, execution: AIAssistantExecution) -> int:
        with self.connection_factory.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO ia_assistente_execucoes (
                    paciente_id, tipo, entrada, resultado, alertas, status, observacoes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    execution.patient_id,
                    execution.request_type.value,
                    execution.input_text,
                    execution.result,
                    execution.alerts,
                    execution.status,
                    execution.notes,
                ),
            )
            return int(cursor.lastrowid)

    def list_executions(self, patient_query: str = "") -> list[AIAssistantExecution]:
        normalized = f"%{patient_query.strip().lower()}%"
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                """
                SELECT ia.id, ia.paciente_id, p.nome AS paciente_nome, ia.tipo,
                       ia.entrada, ia.resultado, ia.alertas, ia.status, ia.observacoes,
                       ia.created_at, ia.updated_at
                FROM ia_assistente_execucoes ia
                LEFT JOIN pacientes p ON p.id = ia.paciente_id
                WHERE ia.deleted_at IS NULL
                  AND (? = '%%' OR lower(coalesce(p.nome, '')) LIKE ?)
                ORDER BY ia.created_at DESC, ia.id DESC
                """,
                (normalized, normalized),
            ).fetchall()
        return [self._row_to_execution(row) for row in rows]

    def _row_to_execution(self, row) -> AIAssistantExecution:
        return AIAssistantExecution(
            id=row["id"],
            patient_id=row["paciente_id"],
            patient_name=row["paciente_nome"] or "",
            request_type=AIAssistantRequestType(row["tipo"]),
            input_text=row["entrada"] or "",
            result=row["resultado"],
            alerts=row["alertas"] or "",
            status=row["status"],
            notes=row["observacoes"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
