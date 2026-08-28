from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class AllergyCategory(StrEnum):
    FOOD = "Alimentar"
    MEDICATION = "Medicamentosa"


@dataclass(frozen=True)
class PatientAllergy:
    patient_id: int
    category: AllergyCategory
    allergen: str
    severity: str = ""
    conduct: str = ""
    notes: str = ""
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
