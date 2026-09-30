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


class FoodGroup(StrEnum):
    CEREAIS_TUBERCULOS = "Cereais e tuberculos"
    LEGUMINOSAS = "Leguminosas"
    CARNES_OVOS = "Carnes e ovos"
    LATICINIOS = "Laticinios"
    HORTALICAS = "Hortalicas"
    FRUTAS = "Frutas"
    GORDURAS_OLEOS = "Gorduras e oleos"
    ACUCARES_DOCES = "Acucares e doces"
    BEBIDAS = "Bebidas"
    OUTROS = "Outros"


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
    allergens: str = ""
    notes: str = ""
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
