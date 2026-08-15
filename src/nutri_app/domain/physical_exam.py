from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class NutritionPhysicalExam:
    patient_id: int
    assessment_date: date
    findings: dict[str, str]
    summary: str
    severity: str
    signs_symptoms: str = ""
    image_path: str = ""
    image_consent: bool = False
    diagnosis_id: int | None = None
    patient_name: str = ""
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
