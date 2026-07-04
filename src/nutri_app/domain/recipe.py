from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class RecipeIngredient:
    name: str
    quantity: float
    unit: str
    weight_g: float
    energy_kcal: float = 0
    protein_g: float = 0
    carbohydrate_g: float = 0
    fat_g: float = 0
    fiber_g: float = 0
    sodium_mg: float = 0
    notes: str = ""
    food_id: int | None = None
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class Recipe:
    name: str
    servings: float
    total_weight_g: float
    category: str = ""
    preparation_method: str = ""
    photo_path: str = ""
    total_energy_kcal: float = 0
    total_protein_g: float = 0
    total_carbohydrate_g: float = 0
    total_fat_g: float = 0
    total_fiber_g: float = 0
    total_sodium_mg: float = 0
    notes: str = ""
    ingredients: list[RecipeIngredient] = field(default_factory=list)
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
