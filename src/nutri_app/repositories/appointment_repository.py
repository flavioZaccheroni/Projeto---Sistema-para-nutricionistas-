from __future__ import annotations

from datetime import date, datetime

from nutri_app.domain.appointment import Appointment, AppointmentKind, AppointmentStatus
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class AppointmentRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def add(self, appointment: Appointment) -> int:
        with self.connection_factory.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO consultas (paciente_id, data_hora, tipo, status, observacoes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    appointment.patient_id,
                    self._format_datetime(appointment.scheduled_at),
                    appointment.kind.value,
                    appointment.status.value,
                    appointment.notes,
                ),
            )
            return int(cursor.lastrowid)

    def update(self, appointment: Appointment) -> None:
        if appointment.id is None:
            raise ValueError("Consulta sem ID nao pode ser atualizada.")

        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE consultas
                SET paciente_id = ?,
                    data_hora = ?,
                    tipo = ?,
                    status = ?,
                    observacoes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (
                    appointment.patient_id,
                    self._format_datetime(appointment.scheduled_at),
                    appointment.kind.value,
                    appointment.status.value,
                    appointment.notes,
                    appointment.id,
                ),
            )

    def set_status(self, appointment_id: int, status: AppointmentStatus) -> None:
        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE consultas
                SET status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (status.value, appointment_id),
            )

    def soft_delete(self, appointment_id: int) -> None:
        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE consultas
                SET deleted_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (appointment_id,),
            )

    def get(self, appointment_id: int) -> Appointment | None:
        with self.connection_factory.connect() as connection:
            row = connection.execute(
                """
                SELECT c.id, c.paciente_id, p.nome AS paciente_nome, c.data_hora,
                       c.tipo, c.status, c.observacoes, c.created_at, c.updated_at
                FROM consultas c
                JOIN pacientes p ON p.id = c.paciente_id
                WHERE c.id = ? AND c.deleted_at IS NULL AND p.deleted_at IS NULL
                """,
                (appointment_id,),
            ).fetchone()

        return self._row_to_appointment(row) if row is not None else None

    def list_by_period(
        self,
        start: date | None = None,
        end: date | None = None,
        status: AppointmentStatus | None = None,
    ) -> list[Appointment]:
        where = ["c.deleted_at IS NULL", "p.deleted_at IS NULL"]
        params: list[str] = []

        if start is not None:
            where.append("substr(c.data_hora, 1, 10) >= ?")
            params.append(start.isoformat())
        if end is not None:
            where.append("substr(c.data_hora, 1, 10) <= ?")
            params.append(end.isoformat())
        if status is not None:
            where.append("c.status = ?")
            params.append(status.value)

        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT c.id, c.paciente_id, p.nome AS paciente_nome, c.data_hora,
                       c.tipo, c.status, c.observacoes, c.created_at, c.updated_at
                FROM consultas c
                JOIN pacientes p ON p.id = c.paciente_id
                WHERE {" AND ".join(where)}
                ORDER BY c.data_hora
                """,
                tuple(params),
            ).fetchall()

        return [self._row_to_appointment(row) for row in rows]

    def _row_to_appointment(self, row) -> Appointment:
        return Appointment(
            id=row["id"],
            patient_id=row["paciente_id"],
            patient_name=row["paciente_nome"],
            scheduled_at=self._parse_datetime(row["data_hora"]),
            kind=AppointmentKind(row["tipo"]),
            status=AppointmentStatus(row["status"]),
            notes=row["observacoes"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _format_datetime(self, value: datetime) -> str:
        return value.strftime("%Y-%m-%d %H:%M")

    def _parse_datetime(self, value: str) -> datetime:
        return datetime.strptime(value, "%Y-%m-%d %H:%M")
