from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class SupplementPrescription:
    patient_id: int
    supplement_id: int
    start_date: date
    end_date: date
    quantity: float
    unit: str
    frequency_per_day: int
    times: str
    objective: str
    instructions: str
    status: str = "Ativa"
    supplement_snapshot: dict[str, object] | None = None
    daily_intake: dict[str, float] | None = None
    patient_name: str = ""
    supplement_name: str = ""
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class SupplementFollowUp:
    prescription_id: int
    record_date: date
    acceptance: int
    adherence_percent: float
    incidents: str = ""
    clinical_response: str = ""
    suspension_reason: str = ""
    id: int | None = None
    created_at: datetime | None = None
