from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


class BodyCompositionProtocol(StrEnum):
    POLLOCK = "Pollock"
    DURNIN_WOMERSLEY = "Durnin & Womersley"
    FAULKNER = "Faulkner"
    PETROSKI = "Petroski"
    GUEDES = "Guedes"
    BIA = "Bioimpedancia"
    DXA = "DXA"


@dataclass(frozen=True)
class BodyComposition:
    patient_id: int
    assessment_date: date
    protocol: BodyCompositionProtocol
    weight_kg: float
    body_fat_percentage: float
    fat_mass_kg: float
    lean_mass_kg: float
    appointment_id: int | None = None
    body_water_percentage: float | None = None
    muscle_mass_kg: float | None = None
    visceral_fat: float | None = None
    notes: str = ""
    id: int | None = None
    patient_name: str = ""
    appointment_label: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
