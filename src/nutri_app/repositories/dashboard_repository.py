from __future__ import annotations

from datetime import date

from nutri_app.domain.dashboard import (
    DashboardAlert,
    DashboardAppointment,
    DashboardSummary,
)
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class DashboardRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def summary(self, today: date | None = None) -> DashboardSummary:
        reference_date = today or date.today()
        with self.connection_factory.connect() as connection:
            active_patients = self._count(
                connection,
                "SELECT COUNT(*) AS total FROM pacientes WHERE deleted_at IS NULL",
            )
            today_appointments = self._count(
                connection,
                """
                SELECT COUNT(*) AS total
                FROM consultas
                WHERE deleted_at IS NULL AND substr(data_hora, 1, 10) = ?
                """,
                (reference_date.isoformat(),),
            )
            critical_alerts = self._count(
                connection,
                """
                SELECT COUNT(*) AS total
                FROM (
                    SELECT id FROM antropometrias
                    WHERE deleted_at IS NULL AND lower(classificacao_imc) LIKE '%baixo%'
                    UNION ALL
                    SELECT id FROM triagens
                    WHERE deleted_at IS NULL AND lower(classificacao) LIKE '%risco%'
                    UNION ALL
                    SELECT id FROM exame_itens
                    WHERE deleted_at IS NULL AND alerta IS NOT NULL AND trim(alerta) <> ''
                )
                """,
            )
            pending_items = self._count(
                connection,
                """
                SELECT COUNT(*) AS total
                FROM consultas
                WHERE deleted_at IS NULL
                  AND lower(status) IN ('pendente', 'agendada', 'confirmada')
                """,
            )

        return DashboardSummary(
            active_patients=active_patients,
            today_appointments=today_appointments,
            critical_alerts=critical_alerts,
            pending_items=pending_items,
        )

    def recent_alerts(self, limit: int = 8) -> list[DashboardAlert]:
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                """
                SELECT p.nome AS paciente, 'Antropometria' AS origem,
                       'IMC classificado como ' || a.classificacao_imc AS mensagem,
                       'Critico' AS gravidade,
                       a.created_at AS data_registro
                FROM antropometrias a
                JOIN pacientes p ON p.id = a.paciente_id
                WHERE a.deleted_at IS NULL
                  AND p.deleted_at IS NULL
                  AND lower(a.classificacao_imc) LIKE '%baixo%'

                UNION ALL

                SELECT p.nome AS paciente, 'Triagem' AS origem,
                       'Triagem ' || t.protocolo || ': ' || t.classificacao AS mensagem,
                       'Atencao' AS gravidade,
                       t.created_at AS data_registro
                FROM triagens t
                JOIN pacientes p ON p.id = t.paciente_id
                WHERE t.deleted_at IS NULL
                  AND p.deleted_at IS NULL
                  AND lower(t.classificacao) LIKE '%risco%'

                UNION ALL

                SELECT p.nome AS paciente, 'Exames' AS origem,
                       e.nome || ': ' || e.alerta AS mensagem,
                       'Critico' AS gravidade,
                       e.created_at AS data_registro
                FROM exame_itens e
                JOIN exames_laboratoriais x ON x.id = e.exame_id
                JOIN pacientes p ON p.id = x.paciente_id
                WHERE e.deleted_at IS NULL
                  AND x.deleted_at IS NULL
                  AND p.deleted_at IS NULL
                  AND e.alerta IS NOT NULL
                  AND trim(e.alerta) <> ''

                ORDER BY data_registro DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            DashboardAlert(
                patient_name=row["paciente"],
                source=row["origem"],
                message=row["mensagem"],
                severity=row["gravidade"],
            )
            for row in rows
        ]

    def upcoming_appointments(self, limit: int = 8) -> list[DashboardAppointment]:
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                """
                SELECT c.id, p.nome AS paciente, c.data_hora, c.tipo, c.status
                FROM consultas c
                JOIN pacientes p ON p.id = c.paciente_id
                WHERE c.deleted_at IS NULL
                  AND p.deleted_at IS NULL
                  AND lower(c.status) IN ('pendente', 'agendada', 'confirmada')
                ORDER BY c.data_hora
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            DashboardAppointment(
                id=row["id"],
                patient_name=row["paciente"],
                scheduled_at=row["data_hora"],
                kind=row["tipo"],
                status=row["status"],
            )
            for row in rows
        ]

    def _count(self, connection, sql: str, params: tuple = ()) -> int:
        row = connection.execute(sql, params).fetchone()
        return int(row["total"])
