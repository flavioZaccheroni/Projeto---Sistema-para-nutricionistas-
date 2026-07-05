from __future__ import annotations

from datetime import date, datetime

from nutri_app.domain.finance import (
    FinancialEntry,
    FinancialEntryType,
    FinancialStatus,
    FinancialSummary,
)
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class FinanceRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def add(self, entry: FinancialEntry) -> int:
        with self.connection_factory.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO financeiro_lancamentos (
                    paciente_id, consulta_id, tipo, categoria, descricao, valor,
                    data_vencimento, data_pagamento, forma_pagamento, status, observacoes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._values(entry),
            )
            return int(cursor.lastrowid)

    def update(self, entry: FinancialEntry) -> None:
        if entry.id is None:
            raise ValueError("Lancamento financeiro sem ID nao pode ser atualizado.")

        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE financeiro_lancamentos
                SET paciente_id = ?,
                    consulta_id = ?,
                    tipo = ?,
                    categoria = ?,
                    descricao = ?,
                    valor = ?,
                    data_vencimento = ?,
                    data_pagamento = ?,
                    forma_pagamento = ?,
                    status = ?,
                    observacoes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (*self._values(entry), entry.id),
            )

    def soft_delete(self, entry_id: int) -> None:
        with self.connection_factory.connect() as connection:
            connection.execute(
                """
                UPDATE financeiro_lancamentos
                SET deleted_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL
                """,
                (entry_id,),
            )

    def get(self, entry_id: int) -> FinancialEntry | None:
        with self.connection_factory.connect() as connection:
            row = connection.execute(
                f"""
                {self._select_sql()}
                WHERE f.id = ? AND f.deleted_at IS NULL
                """,
                (entry_id,),
            ).fetchone()
        return self._row_to_entry(row) if row is not None else None

    def list_active(
        self,
        patient_query: str = "",
        status: FinancialStatus | None = None,
        start: date | None = None,
        end: date | None = None,
    ) -> list[FinancialEntry]:
        where = ["f.deleted_at IS NULL"]
        params: list[object] = []
        normalized = f"%{patient_query.strip().lower()}%"
        where.append("(? = '%%' OR lower(coalesce(p.nome, '')) LIKE ?)")
        params.extend([normalized, normalized])
        if status is not None:
            where.append("f.status = ?")
            params.append(status.value)
        if start is not None:
            where.append("f.data_vencimento >= ?")
            params.append(start.isoformat())
        if end is not None:
            where.append("f.data_vencimento <= ?")
            params.append(end.isoformat())

        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                f"""
                {self._select_sql()}
                WHERE {" AND ".join(where)}
                ORDER BY f.data_vencimento DESC, f.updated_at DESC
                """,
                tuple(params),
            ).fetchall()
        return [self._row_to_entry(row) for row in rows]

    def monthly_summary(self, year: int, month: int) -> FinancialSummary:
        start = date(year, month, 1)
        end = date(year + int(month == 12), 1 if month == 12 else month + 1, 1)
        entries = self.list_active(start=start, end=date.fromordinal(end.toordinal() - 1))
        total_receivable = sum(
            entry.amount for entry in entries if entry.entry_type == FinancialEntryType.RECEIVABLE
        )
        total_payable = sum(
            entry.amount for entry in entries if entry.entry_type == FinancialEntryType.PAYABLE
        )
        total_received = sum(
            entry.amount
            for entry in entries
            if entry.entry_type == FinancialEntryType.RECEIVABLE
            and entry.status == FinancialStatus.PAID
        )
        total_paid = sum(
            entry.amount
            for entry in entries
            if entry.entry_type == FinancialEntryType.PAYABLE
            and entry.status == FinancialStatus.PAID
        )
        total_overdue = sum(
            entry.amount for entry in entries if entry.status == FinancialStatus.OVERDUE
        )
        return FinancialSummary(
            total_receivable=total_receivable,
            total_payable=total_payable,
            total_received=total_received,
            total_paid=total_paid,
            total_overdue=total_overdue,
            open_balance=total_receivable - total_payable,
        )

    def _values(self, entry: FinancialEntry) -> tuple:
        return (
            entry.patient_id,
            entry.appointment_id,
            entry.entry_type.value,
            entry.category,
            entry.description,
            entry.amount,
            entry.due_date.isoformat(),
            entry.payment_date.isoformat() if entry.payment_date is not None else None,
            entry.payment_method,
            entry.status.value,
            entry.notes,
        )

    def _select_sql(self) -> str:
        return """
            SELECT f.id, f.paciente_id, p.nome AS paciente_nome, f.consulta_id,
                   CASE
                       WHEN c.id IS NULL THEN ''
                       ELSE c.data_hora || ' - ' || c.tipo
                   END AS consulta_rotulo,
                   f.tipo, f.categoria, f.descricao, f.valor, f.data_vencimento,
                   f.data_pagamento, f.forma_pagamento, f.status, f.observacoes,
                   f.created_at, f.updated_at
            FROM financeiro_lancamentos f
            LEFT JOIN pacientes p ON p.id = f.paciente_id AND p.deleted_at IS NULL
            LEFT JOIN consultas c ON c.id = f.consulta_id AND c.deleted_at IS NULL
        """

    def _row_to_entry(self, row) -> FinancialEntry:
        return FinancialEntry(
            id=row["id"],
            patient_id=row["paciente_id"],
            patient_name=row["paciente_nome"] or "",
            appointment_id=row["consulta_id"],
            appointment_label=row["consulta_rotulo"] or "",
            entry_type=FinancialEntryType(row["tipo"]),
            category=row["categoria"],
            description=row["descricao"],
            amount=float(row["valor"]),
            due_date=date.fromisoformat(row["data_vencimento"]),
            payment_date=date.fromisoformat(row["data_pagamento"])
            if row["data_pagamento"]
            else None,
            payment_method=row["forma_pagamento"] or "",
            status=FinancialStatus(row["status"]),
            notes=row["observacoes"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
