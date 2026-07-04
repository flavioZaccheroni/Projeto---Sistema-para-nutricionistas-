from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class SupplementType(StrEnum):
    ORAL = "Suplemento oral"
    ENTERAL_FORMULA = "Formula enteral"
    PROTEIN_MODULE = "Modulo proteico"
    CARBOHYDRATE_MODULE = "Modulo carboidrato"
    LIPID_MODULE = "Modulo lipidico"
    FIBER_MODULE = "Modulo fibras"
    MICRONUTRIENT = "Micronutrientes"
    OTHER = "Outro"


@dataclass(frozen=True)
class Supplement:
    name: str
    supplement_type: SupplementType
    base_portion: float = 100
    portion_unit: str = "ml"
    manufacturer: str = ""
    presentation: str = ""
    caloric_density: float | None = None
    osmolarity: float | None = None
    energy_kcal: float = 0
    protein_g: float = 0
    carbohydrate_g: float = 0
    fat_g: float = 0
    fiber_g: float = 0
    sodium_mg: float = 0
    composition: str = ""
    indications: str = ""
    contraindications: str = ""
    notes: str = ""
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
