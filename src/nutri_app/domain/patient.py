from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class Patient:
    name: str
    birth_date: date
    phone: str = ""
    email: str = ""
    health_insurance: str = ""
    document: str = ""
    responsible: str = ""
    clinical_notes: str = ""
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
