from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True)
class MealPlanItem:
    food: str
    quantity: float
    unit: str
    energy_kcal: float = 0
    protein_g: float = 0
    carbohydrate_g: float = 0
    fat_g: float = 0
    substitutions: str = ""
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class Meal:
    name: str
    time: str = ""
    notes: str = ""
    items: list[MealPlanItem] = field(default_factory=list)
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class MealPlan:
    patient_id: int
    start_date: date
    objective: str
    end_date: date | None = None
    target_energy_kcal: float | None = None
    target_protein_g: float | None = None
    target_carbohydrate_g: float | None = None
    target_fat_g: float | None = None
    total_energy_kcal: float = 0
    total_protein_g: float = 0
    total_carbohydrate_g: float = 0
    total_fat_g: float = 0
    notes: str = ""
    meals: list[Meal] = field(default_factory=list)
    appointment_id: int | None = None
    id: int | None = None
    patient_name: str = ""
    appointment_label: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
