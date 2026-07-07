from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class AdvancedClinicalRecord:
    module: str
    record_date: date
    profile: str
    inputs: dict[str, str]
    result: str
    notes: str = ""
    patient_id: int | None = None
    patient_name: str = ""
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
