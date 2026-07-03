from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Anamnesis:
    patient_id: int
    appointment_id: int | None = None
    chief_complaint: str = ""
    current_disease_history: str = ""
    pathological_history: str = ""
    family_history: str = ""
    food_routine: str = ""
    eating_behavior: str = ""
    gastrointestinal_symptoms: str = ""
    notes: str = ""
    id: int | None = None
    patient_name: str = ""
    appointment_label: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
