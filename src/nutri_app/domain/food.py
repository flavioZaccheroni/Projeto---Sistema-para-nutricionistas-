from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class FoodSource(StrEnum):
    TACO = "TACO"
    TBCA = "TBCA"
    REGIONAL = "Regional"
    INDUSTRIALIZED = "Industrializado"
    CUSTOM = "Personalizado"


@dataclass(frozen=True)
class Food:
    name: str
    source: FoodSource
    base_portion_g: float = 100
    category: str = ""
    household_measure: str = ""
    energy_kcal: float = 0
    protein_g: float = 0
    carbohydrate_g: float = 0
    fat_g: float = 0
    fiber_g: float = 0
    sodium_mg: float = 0
    glycemic_index: float | None = None
    micronutrients: str = ""
    notes: str = ""
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
