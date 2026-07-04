from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


class BiologicalSex(StrEnum):
    MALE = "Masculino"
    FEMALE = "Feminino"


class EnergyEquation(StrEnum):
    HARRIS_BENEDICT = "Harris-Benedict"
    MIFFLIN_ST_JEOR = "Mifflin-St Jeor"
    OWEN = "Owen"
    SCHOFIELD = "Schofield"
    FAO_WHO = "FAO/OMS"
    CUNNINGHAM = "Cunningham"
    KATCH_MCARDLE = "Katch-McArdle"
    DRI = "DRIs"


@dataclass(frozen=True)
class EnergyExpenditure:
    patient_id: int
    assessment_date: date
    sex: BiologicalSex
    age_years: int
    weight_kg: float
    height_cm: float
    equation: EnergyEquation
    activity_factor: float
    stress_factor: float
    goal_adjustment_kcal: float
    basal_energy_kcal: float
    total_energy_kcal: float
    protein_g: float
    carbohydrate_g: float
    fat_g: float
    appointment_id: int | None = None
    lean_mass_kg: float | None = None
    notes: str = ""
    id: int | None = None
    patient_name: str = ""
    appointment_label: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
