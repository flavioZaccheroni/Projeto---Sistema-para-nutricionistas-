from __future__ import annotations

from dataclasses import dataclass

from nutri_app.domain.food import Food


@dataclass(frozen=True)
class PortionNutrients:
    energy_kcal: float
    protein_g: float
    carbohydrate_g: float
    fat_g: float
    fiber_g: float
    sodium_mg: float


class FoodService:
    def validate(self, food: Food) -> None:
        if not food.name.strip():
            raise ValueError("Nome do alimento deve ser informado.")
        if food.base_portion_g <= 0:
            raise ValueError("Porcao base deve ser maior que zero.")
        numeric_values = [
            food.energy_kcal,
            food.protein_g,
            food.carbohydrate_g,
            food.fat_g,
            food.fiber_g,
            food.sodium_mg,
        ]
        if any(value < 0 for value in numeric_values):
            raise ValueError("Valores nutricionais nao podem ser negativos.")
        if food.glycemic_index is not None and food.glycemic_index < 0:
            raise ValueError("Indice glicemico nao pode ser negativo.")

    def calculate_portion(self, food: Food, portion_g: float) -> PortionNutrients:
        self.validate(food)
        if portion_g <= 0:
            raise ValueError("Porcao calculada deve ser maior que zero.")
        factor = portion_g / food.base_portion_g
        return PortionNutrients(
            energy_kcal=food.energy_kcal * factor,
            protein_g=food.protein_g * factor,
            carbohydrate_g=food.carbohydrate_g * factor,
            fat_g=food.fat_g * factor,
            fiber_g=food.fiber_g * factor,
            sodium_mg=food.sodium_mg * factor,
        )
