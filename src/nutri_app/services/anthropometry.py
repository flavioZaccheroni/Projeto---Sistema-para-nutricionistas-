from __future__ import annotations

from enum import StrEnum


class BmiClassification(StrEnum):
    THINNESS = "baixo peso"
    NORMAL = "eutrofia"
    OVERWEIGHT = "sobrepeso"
    OBESITY_I = "obesidade grau I"
    OBESITY_II = "obesidade grau II"
    OBESITY_III = "obesidade grau III"


class AnthropometryService:
    def calculate_bmi(self, weight_kg: float, height_meters: float) -> float:
        if weight_kg <= 0 or height_meters <= 0:
            raise ValueError("Peso e altura devem ser maiores que zero.")
        return weight_kg / (height_meters**2)

    def classify_adult_bmi(self, bmi: float) -> BmiClassification:
        if bmi < 18.5:
            return BmiClassification.THINNESS
        if bmi < 25:
            return BmiClassification.NORMAL
        if bmi < 30:
            return BmiClassification.OVERWEIGHT
        if bmi < 35:
            return BmiClassification.OBESITY_I
        if bmi < 40:
            return BmiClassification.OBESITY_II
        return BmiClassification.OBESITY_III

    def calculate_weight_loss_percentage(
        self,
        usual_weight_kg: float,
        current_weight_kg: float,
    ) -> float:
        if usual_weight_kg <= 0 or current_weight_kg <= 0:
            raise ValueError("Pesos devem ser maiores que zero.")
        return ((usual_weight_kg - current_weight_kg) / usual_weight_kg) * 100

    def has_high_nutritional_risk_by_weight_loss(self, percentage: float) -> bool:
        return percentage > 10
