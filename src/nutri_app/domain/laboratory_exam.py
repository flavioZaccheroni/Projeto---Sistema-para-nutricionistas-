from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True)
class LaboratoryExamItem:
    name: str
    value: float | None = None
    unit: str = ""
    reference: str = ""
    alert: str = ""
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class LaboratoryExam:
    patient_id: int
    exam_date: date
    laboratory: str = ""
    notes: str = ""
    items: list[LaboratoryExamItem] = field(default_factory=list)
    appointment_id: int | None = None
    id: int | None = None
    patient_name: str = ""
    appointment_label: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
