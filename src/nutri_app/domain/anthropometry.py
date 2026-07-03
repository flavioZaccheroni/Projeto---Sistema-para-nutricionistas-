from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class Anthropometry:
    patient_id: int
    assessment_date: date
    weight_kg: float
    height_m: float
    bmi: float
    bmi_classification: str
    appointment_id: int | None = None
    waist_cm: float | None = None
    hip_cm: float | None = None
    waist_hip_ratio: float | None = None
    waist_height_ratio: float | None = None
    notes: str = ""
    id: int | None = None
    patient_name: str = ""
    appointment_label: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
