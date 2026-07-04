from __future__ import annotations

from dataclasses import dataclass

from nutri_app.domain.supplement import Supplement


@dataclass(frozen=True)
class SupplementDose:
    energy_kcal: float
    protein_g: float
    carbohydrate_g: float
    fat_g: float
    fiber_g: float
    sodium_mg: float


class SupplementService:
    def validate(self, supplement: Supplement) -> None:
        if not supplement.name.strip():
            raise ValueError("Nome do suplemento deve ser informado.")
        if supplement.base_portion <= 0:
            raise ValueError("Porcao base deve ser maior que zero.")
        if not supplement.portion_unit.strip():
            raise ValueError("Unidade da porcao deve ser informada.")
        if supplement.caloric_density is not None and supplement.caloric_density < 0:
            raise ValueError("Densidade calorica nao pode ser negativa.")
        if supplement.osmolarity is not None and supplement.osmolarity < 0:
            raise ValueError("Osmolaridade nao pode ser negativa.")
        values = [
            supplement.energy_kcal,
            supplement.protein_g,
            supplement.carbohydrate_g,
            supplement.fat_g,
            supplement.fiber_g,
            supplement.sodium_mg,
        ]
        if any(value < 0 for value in values):
            raise ValueError("Valores nutricionais nao podem ser negativos.")

    def calculate_dose(self, supplement: Supplement, dose: float) -> SupplementDose:
        self.validate(supplement)
        if dose <= 0:
            raise ValueError("Dose deve ser maior que zero.")
        factor = dose / supplement.base_portion
        return SupplementDose(
            energy_kcal=supplement.energy_kcal * factor,
            protein_g=supplement.protein_g * factor,
            carbohydrate_g=supplement.carbohydrate_g * factor,
            fat_g=supplement.fat_g * factor,
            fiber_g=supplement.fiber_g * factor,
            sodium_mg=supplement.sodium_mg * factor,
        )
