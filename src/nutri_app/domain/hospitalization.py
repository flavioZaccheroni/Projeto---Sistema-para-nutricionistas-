from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class Hospitalization:
    patient_id: int
    admission_date: date
    unit: str
    ward: str = ""
    bed: str = ""
    health_insurance: str = ""
    responsible_team: str = ""
    diagnoses: str = ""
    discharge_date: date | None = None
    discharge_condition: str = ""
    status: str = "Ativa"
    notes: str = ""
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
