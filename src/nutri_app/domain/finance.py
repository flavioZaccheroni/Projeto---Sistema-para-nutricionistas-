from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


class FinancialEntryType(StrEnum):
    RECEIVABLE = "Recebimento"
    PAYABLE = "Pagamento"


class FinancialStatus(StrEnum):
    OPEN = "Aberto"
    PAID = "Pago"
    OVERDUE = "Vencido"
    CANCELED = "Cancelado"


@dataclass(frozen=True)
class FinancialEntry:
    entry_type: FinancialEntryType
    category: str
    description: str
    amount: float
    due_date: date
    status: FinancialStatus = FinancialStatus.OPEN
    patient_id: int | None = None
    patient_name: str = ""
    appointment_id: int | None = None
    appointment_label: str = ""
    payment_date: date | None = None
    payment_method: str = ""
    notes: str = ""
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class FinancialSummary:
    total_receivable: float = 0
    total_payable: float = 0
    total_received: float = 0
    total_paid: float = 0
    total_overdue: float = 0
    open_balance: float = 0
