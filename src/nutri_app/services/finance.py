from __future__ import annotations

from datetime import date

from nutri_app.domain.finance import FinancialEntry, FinancialEntryType, FinancialStatus


class FinanceService:
    def normalize_status(
        self,
        entry: FinancialEntry,
        reference_date: date | None = None,
    ) -> FinancialStatus:
        today = reference_date or date.today()
        if entry.status == FinancialStatus.CANCELED:
            return FinancialStatus.CANCELED
        if entry.payment_date is not None:
            return FinancialStatus.PAID
        if entry.due_date < today:
            return FinancialStatus.OVERDUE
        return FinancialStatus.OPEN

    def validate(self, entry: FinancialEntry) -> None:
        if not entry.description.strip():
            raise ValueError("Descricao do lancamento e obrigatoria.")
        if not entry.category.strip():
            raise ValueError("Categoria do lancamento e obrigatoria.")
        if entry.amount <= 0:
            raise ValueError("Valor deve ser maior que zero.")
        if entry.status == FinancialStatus.PAID and entry.payment_date is None:
            raise ValueError("Lancamento pago precisa de data de pagamento.")

    def signed_amount(self, entry: FinancialEntry) -> float:
        if entry.entry_type == FinancialEntryType.RECEIVABLE:
            return entry.amount
        return -entry.amount
