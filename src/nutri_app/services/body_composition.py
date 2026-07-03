from __future__ import annotations


class BodyCompositionService:
    def calculate_fat_mass(self, weight_kg: float, body_fat_percentage: float) -> float:
        self._validate(weight_kg, body_fat_percentage)
        return weight_kg * (body_fat_percentage / 100)

    def calculate_lean_mass(self, weight_kg: float, body_fat_percentage: float) -> float:
        fat_mass = self.calculate_fat_mass(weight_kg, body_fat_percentage)
        return weight_kg - fat_mass

    def _validate(self, weight_kg: float, body_fat_percentage: float) -> None:
        if weight_kg <= 0:
            raise ValueError("Peso deve ser maior que zero.")
        if body_fat_percentage < 0 or body_fat_percentage > 100:
            raise ValueError("Percentual de gordura deve estar entre 0 e 100.")
